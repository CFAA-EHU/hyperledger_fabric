package chaincode

import (
	"encoding/json"
	"fmt"
	"log"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing a Record
type SmartContract struct {
	contractapi.Contract
}

// Record describes basic details of what makes up a simple record
type Record struct {
	Timestamp string `json:"timestamp"`
        IntervalStart string `json:"intervalStart"`
        IntervalEnd string `json:"intervalEnd"`
        Program string `json:"program"`
	FileHash  string `json:"fileHash"`
}

// InitLedger adds a base set of records to the ledger
func (s *SmartContract) InitLedger(ctx contractapi.TransactionContextInterface) error {
	records := []Record{
		{Timestamp: "1741334401", IntervalStart: "1741330800", IntervalEnd: "1741334400", Program: "ProgramaInit", FileHash: "hashInit"},
	}

	for _, record := range records {
		recordJSON, err := json.Marshal(record)
		if err != nil {
			return err
		}

		err = ctx.GetStub().PutState(record.Timestamp, recordJSON)
		if err != nil {
			return fmt.Errorf("failed to put to world state. %v", err)
		}
	}

	return nil
}

// CreateRecord issues a new record to the world state with given details.
func (s *SmartContract) CreateRecord(ctx contractapi.TransactionContextInterface, timestamp string, intervalStart string ,intervalEnd string, program string, fileHash string) error {
	exists, err := s.RecordExists(ctx, timestamp)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("the record %s already exists", timestamp)
	}

	// Get current timestamp
	// timeSegundos := time.Now().Unix()

	record := Record{
		Timestamp:  timestamp,
                IntervalStart:  intervalStart,
                IntervalEnd:  intervalEnd,
		Program:  program,
		FileHash: fileHash,
	}
	recordJSON, err := json.Marshal(record)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(timestamp, recordJSON)
}

// ReadRecord returns the record stored in the world state with given timestamp.
func (s *SmartContract) ReadRecord(ctx contractapi.TransactionContextInterface, timestamp string) (*Record, error) {
	recordJSON, err := ctx.GetStub().GetState(timestamp)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if recordJSON == nil {
		return nil, fmt.Errorf("the record %s does not exist", timestamp)
	}

	var record Record
	err = json.Unmarshal(recordJSON, &record)
	if err != nil {
		return nil, err
	}

	return &record, nil
}

// UpdateRecord updates an existing record in the world state with provided parameters.
func (s *SmartContract) UpdateRecord(ctx contractapi.TransactionContextInterface, timestamp string, intervalStart string ,intervalEnd string, program string, fileHash string) error {
	exists, err := s.RecordExists(ctx, timestamp)
	if err != nil {
		return err
	}
	if !exists {
		return fmt.Errorf("the record %s does not exist", timestamp)
	}

	// Get current timestamp
	// timeSegundos := time.Now().Unix()

	// Overwriting original record with new record
	record := Record{
		Timestamp:  timestamp,
                IntervalStart:  intervalStart,
                IntervalEnd:  intervalEnd,
                Program:  program,
		FileHash:  fileHash,
	}
	recordJSON, err := json.Marshal(record)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(timestamp, recordJSON)
}

// DeleteRecord deletes a given record from the world state.
func (s *SmartContract) DeleteRecord(ctx contractapi.TransactionContextInterface, timestamp string) error {
	exists, err := s.RecordExists(ctx, timestamp)
	if err != nil {
		return err
	}
	if !exists {
		return fmt.Errorf("the record %s does not exist", timestamp)
	}

	return ctx.GetStub().DelState(timestamp)
}

// RecordExists returns true when record with given timestamp exists in world state
func (s *SmartContract) RecordExists(ctx contractapi.TransactionContextInterface, timestamp string) (bool, error) {
	recordJSON, err := ctx.GetStub().GetState(timestamp)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}

	return recordJSON != nil, nil
}


// GetAllRecords returns all records found in world state
func (s *SmartContract) GetAllRecords(ctx contractapi.TransactionContextInterface) ([]*Record, error) {
	// range query with empty string for startKey and endKey does an
	// open-ended query of all records in the chaincode namespace.
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var records []*Record
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var record Record
		err = json.Unmarshal(queryResponse.Value, &record)
		if err != nil {
			return nil, err
		}
		records = append(records, &record)
	}

	return records, nil
}


func main() {
        chaincode, err := contractapi.NewChaincode(new(SmartContract))
        if err != nil {
                log.Panicf("Error creating chaincode: %v", err)
        }

        if err := chaincode.Start(); err != nil {
                log.Panicf("Error starting chaincode: %v", err)
        }
}
