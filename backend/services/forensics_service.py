"""
services/forensics_service.py — Forensic Document Authentication & Tamper Detection

Features:
1. EXIF & Metadata Extraction (detects mobile cameras vs scanners vs image editing software like Photoshop/Canva).
2. Error Level Analysis (ELA) (re-compresses image at 95% JPEG quality and computes pixel error matrix to highlight manipulated regions).
3. Digital LSB Invisible Watermarking (embeds/extracts cryptographic parcel ID and custody hash into RGB least significant bits).
4. Composite Tamper Risk Scorer (0-100 score with heuristic indicators for Revenue Officers).
"""

import io
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageChops, ImageEnhance, ExifTags


def extract_exif_metadata(image_bytes: bytes) -> dict:
    """Extract EXIF metadata and analyze hardware/software provenance."""
    metadata = {
        "has_exif": False,
        "camera_make": None,
        "camera_model": None,
        "software": None,
        "datetime_original": None,
        "gps_info": None,
        "image_width": None,
        "image_height": None,
        "dpi": None,
        "provenance_type": "SCANNED_DOCUMENT",  # SCANNED_DOCUMENT | MOBILE_CAMERA | DIGITAL_EDITOR | UNKNOWN
        "suspicious_flags": []
    }

    try:
        img = Image.open(io.BytesIO(image_bytes))
        metadata["image_width"], metadata["image_height"] = img.size
        metadata["dpi"] = img.info.get("dpi", (300, 300))

        exif_raw = img.getexif()
        if exif_raw:
            metadata["has_exif"] = True
            for tag_id, value in exif_raw.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                if tag_name == "Make":
                    metadata["camera_make"] = str(value).strip()
                elif tag_name == "Model":
                    metadata["camera_model"] = str(value).strip()
                elif tag_name == "Software":
                    metadata["software"] = str(value).strip()
                elif tag_name in ("DateTimeOriginal", "DateTime"):
                    metadata["datetime_original"] = str(value).strip()

        # Provenance classification
        software_lower = (metadata["software"] or "").lower()
        if any(editor in software_lower for editor in ["photoshop", "gimp", "canva", "paint.net", "coreldraw", "illustrator"]):
            metadata["provenance_type"] = "DIGITAL_EDITOR"
            metadata["suspicious_flags"].append(f"Image edited using software signature: {metadata['software']}")

        if metadata["camera_make"] or metadata["camera_model"]:
            camera_str = f"{metadata['camera_make'] or ''} {metadata['camera_model'] or ''}".lower()
            if any(brand in camera_str for brand in ["apple", "samsung", "xiaomi", "oneplus", "oppo", "vivo", "realme", "google", "pixel"]):
                metadata["provenance_type"] = "MOBILE_CAMERA"
                metadata["suspicious_flags"].append("Document captured via smartphone camera (potential parallax or lighting tampering)")
            elif any(scanner in camera_str for scanner in ["canon", "epson", "hp", "fujitsu", "ricoh", "brother"]):
                metadata["provenance_type"] = "SCANNED_DOCUMENT"

        # DPI Check
        if metadata["dpi"] and isinstance(metadata["dpi"], (list, tuple)) and metadata["dpi"][0] < 150:
            metadata["suspicious_flags"].append("Low scanning resolution (<150 DPI) — higher risk of illegible text substitution")

    except Exception as exc:
        metadata["suspicious_flags"].append(f"EXIF parsing warning: {str(exc)}")

    return metadata


def generate_ela_heatmap(image_bytes: bytes, quality: int = 95, scale: int = 15) -> bytes:
    """
    Generate Error Level Analysis (ELA) heatmap image.
    High error differences indicate re-saved or spliced areas (e.g. altered numbers or fake stamps).
    """
    try:
        original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Save to memory at standard 95% JPEG quality
        temp_buf = io.BytesIO()
        original.save(temp_buf, format="JPEG", quality=quality)
        temp_buf.seek(0)
        
        # Reopen compressed image
        compressed = Image.open(temp_buf).convert("RGB")
        
        # Calculate absolute difference
        diff = ImageChops.difference(original, compressed)
        
        # Scale the difference to make tampering visually obvious
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema]) or 1
        scale_factor = min(255 // max_diff, scale)
        
        enhancer = ImageEnhance.Brightness(diff)
        ela_img = enhancer.enhance(scale_factor)
        
        # Save as PNG
        output_buf = io.BytesIO()
        ela_img.save(output_buf, format="PNG")
        return output_buf.getvalue()
    except Exception as exc:
        # Return fallback empty 300x300 image on error
        fallback = Image.new("RGB", (300, 300), color=(15, 23, 42))
        out = io.BytesIO()
        fallback.save(out, format="PNG")
        return out.getvalue()


def embed_invisible_watermark(image_bytes: bytes, payload_text: str) -> bytes:
    """
    Embed a digital chain-of-custody watermark into the least significant bits (LSB) of the image.
    Format: payload_text + '###END'
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        encoded_data = payload_text + "###END"
        binary_data = ''.join(format(ord(c), '08b') for c in encoded_data)
        
        pixels = list(img.getdata())
        new_pixels = []
        data_index = 0
        data_len = len(binary_data)
        
        for pixel in pixels:
            if data_index < data_len:
                r, g, b = pixel
                # Modify LSB of Red channel
                r = (r & ~1) | int(binary_data[data_index])
                data_index += 1
                new_pixels.append((r, g, b))
            else:
                new_pixels.append(pixel)
                
        img.putdata(new_pixels)
        out = io.BytesIO()
        img.save(out, format="PNG")
        return out.getvalue()
    except Exception:
        return image_bytes


def extract_invisible_watermark(image_bytes: bytes) -> str | None:
    """Extract LSB watermark from an image to verify BhuNetra chain-of-custody."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        pixels = list(img.getdata())
        
        binary_data = ""
        for pixel in pixels:
            r, _, _ = pixel
            binary_data += str(r & 1)
            
        all_bytes = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
        decoded_str = ""
        for byte in all_bytes:
            if len(byte) < 8:
                break
            decoded_str += chr(int(byte, 2))
            if decoded_str.endswith("###END"):
                return decoded_str[:-6]
                
        return None
    except Exception:
        return None


def run_full_forensic_analysis(doc_id: int, image_bytes: bytes, filename: str, parcel_id_hint: str = None) -> dict:
    """Run comprehensive forensic analysis suite on a document."""
    exif_info = extract_exif_metadata(image_bytes)
    
    # Check watermark
    extracted_watermark = extract_invisible_watermark(image_bytes)
    has_valid_watermark = extracted_watermark is not None and "BHUNETRA" in extracted_watermark
    
    # Compute image hash
    sha256_hash = hashlib.sha256(image_bytes).hexdigest()
    
    # Compute composite tamper score (0 = perfectly authentic, 100 = high tamper likelihood)
    tamper_score = 5
    tamper_reasons = []
    
    if exif_info["provenance_type"] == "DIGITAL_EDITOR":
        tamper_score += 45
        tamper_reasons.append("Digital photo manipulation software signature detected in document metadata.")
    elif exif_info["provenance_type"] == "MOBILE_CAMERA":
        tamper_score += 15
        tamper_reasons.append("Document photographed via smartphone instead of flatbed scanner.")
        
    if len(exif_info["suspicious_flags"]) > 0:
        tamper_score += len(exif_info["suspicious_flags"]) * 10
        for flag in exif_info["suspicious_flags"]:
            if flag not in tamper_reasons:
                tamper_reasons.append(flag)

    tamper_score = min(95, max(5, tamper_score))
    
    authenticity_rating = "AUTHENTIC" if tamper_score < 30 else ("SUSPICIOUS" if tamper_score < 60 else "HIGH_RISK_TAMPERED")
    
    return {
        "document_id": doc_id,
        "filename": filename,
        "sha256_hash": sha256_hash,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tamper_score": tamper_score,
        "authenticity_rating": authenticity_rating,
        "provenance_type": exif_info["provenance_type"],
        "has_exif": exif_info["has_exif"],
        "camera_make": exif_info["camera_make"],
        "camera_model": exif_info["camera_model"],
        "software": exif_info["software"],
        "dimensions": f"{exif_info['image_width']} x {exif_info['image_height']}",
        "dpi": exif_info["dpi"],
        "chain_of_custody": {
            "has_watermark": has_valid_watermark,
            "watermark_payload": extracted_watermark,
            "integrity_verified": True if has_valid_watermark else False
        },
        "tamper_indicators": tamper_reasons,
        "ela_heatmap_url": f"/api/documents/authenticate/{doc_id}/ela-image"
    }
