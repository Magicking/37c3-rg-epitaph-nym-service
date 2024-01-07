import base64
import json
from json import JSONDecodeError
from web3 import Web3
import json
        

import websocket

import utils
from datetime import datetime
import traceback
import rel

self_address_request = json.dumps({
    "type": "selfAddress"
})

CMD_NEW_TEXT = "newText"
CMD_GET_TEXT = "getText"
CMD_GET_PING = "ping"

NYM_KIND_TEXT = b'\x00'  # uint8
NYM_KIND_BINARY = b'\x01'

NYM_HEADER_SIZE_TEXT = b'\x00' * 6  # set to 0 if it's a text
NYM_HEADER_BINARY = b'\x00' * 8  # not used now, to investigate later

HEADER_TEXT_PLAIN_BYTE=b")"
HEADER_APPLICATION_JSON_BYTE=b"."

# to modify, cleaner solution
HEADER_APPLICATION_JSON="{\"mimeType\":\"application/json\",\"headers\":null}"
TOTAL_HEADERS_PAD_SIZE = len(HEADER_APPLICATION_JSON)+len(NYM_HEADER_SIZE_TEXT)+len(HEADER_APPLICATION_JSON_BYTE)+1
class Serve:

    @staticmethod
    def createPayload(recipientData, reply_message, sendRaw):
        if sendRaw:
            message = json.dumps(reply_message, default=str)
        else:
            headers = HEADER_APPLICATION_JSON
            padding = (NYM_KIND_TEXT + NYM_HEADER_SIZE_TEXT + HEADER_APPLICATION_JSON_BYTE).decode('utf-8')
            message = padding + headers + json.dumps(reply_message)

        dataToSend = {
            "type": "reply",
            "message": message,
        }

        dataToSend.update(recipientData)

        return json.dumps(dataToSend)

    def __init__(self):
        url = f"ws://{utils.NYM_CLIENT_ADDR}/"
        self.firstRun = True
        inputs = [['0x0000000000000000000000000000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000000000000000000000000000', '0x00000000000000000000000007000000000000000000000000000000f8000000', '0x0000000000000000000000078000000000000000000000000000003800000000', '0x0000000000000000000001c00000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000000000000000000000000000', '0x0000000000000000000000000000000000000000000000000000000000000000'], '0xa5c972', '']
        self.sendEpitaph(inputs)
        # START APPLICATION HERE
        #self.pasteNym = PasteNym()

        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(url,
                                         on_message=lambda ws, msg: self.on_message(
                                             ws, msg),
                                         on_error=lambda ws, msg: self.on_error(
                                             ws, msg),
                                         on_close=lambda ws: self.on_close(
                                             ws),
                                         on_open=lambda ws: self.on_open(ws),
                                         on_pong=lambda ws, msg: self.on_pong(ws, msg)
                                         )

        # Set dispatcher to automatic reconnection

        self.ws.run_forever(dispatcher=rel, ping_interval=30, ping_timeout=10)

        rel.signal(2, rel.abort)  # Keyboard Interrupt
        rel.dispatch()
        self.ws.close()

    def on_pong(self, ws, msg):
        ws.send(self_address_request)

    def on_open(self, ws):
        self.ws.send(self_address_request)

    def on_error(self, ws, message):
        try:
            print(f"Error ws: {message}")
            traceback.print_exc()
        except UnicodeDecodeError as e:
            print(f"Unicode error, nothing to do about: {e}")
            return
        finally:
            self.ws.close()
            exit(1)

    def on_close(self, ws):
        print(f"Connection to nym-client closed")

    def on_message(self, ws, message):
        message = str(message).replace(u"\\u0000", "")
        try:
            if self.firstRun:
                self.getSelfAddress(message)
                self.firstRun = False
                return

            try:
                received_message = json.loads(message)
            except JSONDecodeError as e:
                traceback.print_exc()
                return

            # test if it's ping answer message
            if received_message.get('address'):
                return

        except UnicodeDecodeError as e:
            print(f"Unicode error, nothing to do about: {e}")
            return

        try:
            print(received_message)
            received_data, isRaw = Serve.getPayload(received_message)
            print(received_data)
            recipient = Serve.getRecipient(received_message)
            print(recipient)
        except TypeError as e:
            print(f"got an error with received payload, {e}")
            return

        print("TODO SEND TRANSACTION HERE with input")
        print(received_data)
        if recipient is None:
            print(f"no recipient found in {received_message}")
            return
        if received_data is not None:
            if utils.DEBUG:
                print(f"-> Got {received_message}")
            else:
                print(f"-> Got {event} from {recipient}")
            data = received_data
            self.sendEpitaph(data)
        else:
            self.error(recipient, message, received_message, "received data is empty")
            return

#       Do not send reply
#        if event == CMD_NEW_TEXT:
#            reply = self.newText(data)
#        elif event == CMD_GET_TEXT:
#            reply = self.getText(data)
#        elif event == CMD_GET_PING:
#            reply = self.getVersion()
#        else:
#            reply = f"Error event {event} not found"
#
#        if utils.DEBUG:
#            print(f"-> Rcv {event} - answers {reply} over the mix network.")
#        else:
#            print(f"-> Rcv {event} - answers to {recipient} over the mix network.")
#
#        self.ws.send(Serve.createPayload(recipient, reply, sendRaw=isRaw))


    def newText(self, message):
        if "text" in message.keys():
            if len(message.get('text')) <= utils.PASTE_MAX_LENGTH:
                urlId = self.pasteNym.newText(message)

                if urlId is not None:
                    try:
                        if len(urlId) > 0:
                            reply_message = {"ipfs": False}
                            if urlId[0].get('is_ipfs'):
                                reply_message['ipfs'] = urlId[0].get('is_ipfs')
                                reply_message.update({"hash": urlId[0].get('url_id')})

                            reply_message.update({"url_id": urlId[0].get('url_id')})
                        else:
                            reply_message = "Error"
                    except IndexError as e:
                        print(e)
                        reply_message = "Error"
                else:
                    reply_message = "Error with text to share"
            else:
                reply_message = f"Error text too long. Max is {utils.PASTE_MAX_LENGTH}"
        else:
            reply_message = "Message has no text!"

        return reply_message

    def sendEpitaph(self, inputs):
        print("HERE1")
        # Load ABI and configuration
        with open('contract_abi.json') as abi_file:
            contract_abi = json.load(abi_file)
        
        with open('rge.conf.json') as config_file:
            config_data = json.load(config_file)
        
        contract_address = config_data['address']
        ethereum_rpc_url = config_data['rpc']
        
        # Connect to Ethereum node
        web3 = Web3(Web3.HTTPProvider(ethereum_rpc_url))
        
        # Ensure connection is successful
        if not web3.is_connected():
            raise Exception("Failed to connect to Ethereum node")
        
        print("HERE2")
        # Create contract instance
        contract = web3.eth.contract(address=contract_address, abi=contract_abi)
        
        # Prepare transaction

        print("HERE21")
        inputs[0]=[int.from_bytes(bytes.fromhex(x[2:]),"big") for x in inputs[0]]
        if len(inputs[0])!=12:
            raise Exception("Invalid input")
        inputs[1]=int.from_bytes(bytes.fromhex(inputs[1][2:]), "big")
        #print(dir(contract.functions.mintEpitaph(inputs[0],inputs[1],inputs[2])))
        params = (inputs[0],inputs[1],inputs[2] if inputs[2] != '' else b"")
        # Convert params to abi format

        print(params)
        print("HERE3")
        print(dir(contract.functions.mintEpitaph(*params)))
        transaction = contract.functions.mintEpitaph([*params[0]],params[1],params[2]).build_transaction({
            'chainId': 1, # Mainnet
            'gas': 2000000,
            'gasPrice': web3.to_wei('50', 'gwei'),
            'value': web3.to_wei('2', 'ether'),
            'nonce': web3.eth.get_transaction_count('0x976EA74026E726554dB657fA54763abd0C3a0aa9')
        })
        print()
        print()
        print("HERE4")
        print(transaction)
        
        # Sign and send the transaction
        private_key = '0x92db14e403b83dfe3df233f83dfa3a0d7096f21ca9b0d6d6b8d88b2b4ec1564e'
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
        txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Output the transaction hash
        print(f"Transaction sent with hash: {txn_hash.hex()}")

    def getText(self, message):
        text = self.pasteNym.getTextById(message)

        try:
            if text is not None:

                # append a Z to be in iso format that JS Date can understand
                createdOn = text.get('created_on')

                if type(createdOn) == str:

                    # remove the microseconds
                    text['created_on'] = datetime.strptime(createdOn.split(".")[0], "%Y-%m-%dT%H:%M:%S")

                elif createdOn is not None:
                    text['created_on'] = datetime.isoformat(
                        createdOn) + 'Z'

                if text.get('expiration_time'):
                    text['expiration_time'] = datetime.isoformat(
                        text['expiration_time']) + 'Z'

                reply_message = text

            else:
                reply_message = json.dumps({"error": "text not found"})
        except IndexError as e:
            print(e)
            reply_message = "error"

        return reply_message

    def getVersion(self):

        capabilities = {}
        reply_message = {"version": utils.VERSION, "alive": True, "capabilities": capabilities}
        return reply_message

    def error(self, recipient, message, received_message, error):
        if recipient is not None:
            err_msg = f"Error parsing message: {error}"
            reply_message = err_msg
            self.ws.send(Serve.createPayload(recipient, reply_message, sendRaw=True))
            print(f"send error message, data received {message}")
            return
        else:
            print(f"No recipient found in message {received_message}")
            return None

    @staticmethod
    def getRecipient(received_message):
        recipient = received_message.get('senderTag')
        if recipient is None:
            return None

        return {"senderTag": recipient}
    @staticmethod
    def getPayload(received_message):
        # try to json decode, if it works it mean sendRaw is used
        raw = False
        try:
            raw = True
            kS1 = received_message['message'].find('[')
            kS2 = received_message['message'].find(']')
            kS2 = received_message['message'].find(']', kS2+1)
            toDecode = received_message['message'][kS1:kS2+1]
            print(toDecode)
            transaction_inputs = json.loads(toDecode)

            return transaction_inputs, raw
        except (JSONDecodeError, UnicodeDecodeError) as e:
            print(f"cannot decode message received, {e}")

        return None


    def getSelfAddress(self,message):
        try:
            self_address = json.loads(message)
        except JSONDecodeError as e:
            print(f"error decoding self address, {e}")
            return

        try:
            print("Our address is: {}".format(self_address["address"]))
        except ValueError as e:
            print(f"error decoding self address, {e}")
            return
