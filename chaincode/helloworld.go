package main

import (
	"encoding/json"
	"fmt"
	"github.com/hyperledger/fabric/core/chaincode/shim"
	pb "github.com/hyperledger/fabric/protos/peer"
	"time"
)

type SimpleChaincode struct {
}

var logger = shim.NewLogger("HELLOWORLD_CHAINCODE")

// Consent Events
type Event struct {
	EventTime time.Time `json:"eventTime"` // Time when the event is committed
	TxID      string    `json:"txID"`      // The ID of the transaction that wrote the event
	Statement string    `json:"statement"`
}

// ===================================================================================
// Main
// ===================================================================================
func main() {
	err := shim.Start(new(SimpleChaincode))
	if err != nil {
		fmt.Printf("Error starting Simple chaincode: %s", err)
	}
}

// Init initializes chaincode
// ===========================
func (t *SimpleChaincode) Init(stub shim.ChaincodeStubInterface) pb.Response {
	return shim.Success(nil)
}

// Invoke - Our entry point for Invocations
// ========================================
func (t *SimpleChaincode) Invoke(stub shim.ChaincodeStubInterface) pb.Response {
	function, args := stub.GetFunctionAndParameters()
	if function == "makeStatement" {
		if len(args) != 1 {
			return shim.Error("Incorrect number of arguments: " + string(len(args)))
		}
		statement := args[0]
		ts, _ := stub.GetTxTimestamp()
		txtime := time.Unix(ts.Seconds, int64(ts.Nanos))
		event := Event{
			Statement: statement,
			EventTime: txtime,
			TxID:      stub.GetTxID(),
		}
		evtJson, _ := json.Marshal(event)
		stub.PutState(stub.GetTxID(), evtJson)
		return shim.Success(evtJson)
	}
	logger.Errorf("invoke did not find func: %s", function)
	return shim.Error("Received unknown function invocation")
}
