// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title LandRecordHasher
 * @dev Permissioned smart contract for BhuNetra AI land record approval hashing.
 * Stores immutable SHA-256 hashes of Revenue Officer approved/overridden records.
 * Spatial geometries remain indexed in PostGIS; only immutable approval hashes live on-chain.
 */
contract LandRecordHasher {

    struct ApprovalRecord {
        string parcelId;
        string recordHash;
        string approvedBy;
        string action;
        string reason;
        uint256 timestamp;
    }

    // Mapping from parcelId to array of approval hashes
    mapping(string => ApprovalRecord[]) private _parcelHistory;
    
    // Total hashes recorded
    uint256 public totalApprovals;

    event LandRecordApproved(
        string indexed parcelId,
        string recordHash,
        string approvedBy,
        string action,
        uint256 timestamp
    );

    function recordApproval(
        string memory parcelId,
        string memory recordHash,
        string memory approvedBy,
        string memory action,
        string memory reason
    ) public returns (bool) {
        ApprovalRecord memory record = ApprovalRecord({
            parcelId: parcelId,
            recordHash: recordHash,
            approvedBy: approvedBy,
            action: action,
            reason: reason,
            timestamp: block.timestamp
        });

        _parcelHistory[parcelId].push(record);
        totalApprovals++;

        emit LandRecordApproved(parcelId, recordHash, approvedBy, action, block.timestamp);
        return true;
    }

    function getParcelApprovalHistory(string memory parcelId)
        public
        view
        returns (ApprovalRecord[] memory)
    {
        return _parcelHistory[parcelId];
    }
}
