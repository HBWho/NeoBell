import paho.mqtt.client as mqtt
import ssl
import time
import os
from dotenv import load_dotenv

load_dotenv()

AWS_IOT_ENDPOINT = os.getenv("AWS_IOT_ENDPOINT")
PORT = os.getenv("PORT")
CLIENT_ID = os.getenv("CLIENT_ID")

# Paths to your certificate files on the Radxa
ROOT_CA_PATH = "certifications/AmazonRootCA1.pem"
DEVICE_CERT_PATH = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-certificate.pem.crt"
PRIVATE_KEY_PATH = "certifications/10da83970c7ac9793d1f4c33c48f082924dc1aaccd0e8e8fd229d13b5caa210e-private.pem.key"

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc, properties=None):
    # ... (your existing on_connect code is likely fine) ...
    print(f"on_connect called. Client: {client}, Userdata: {userdata}, Flags: {flags}, Result Code (rc): {rc}, Properties: {properties}")
    if rc == 0:
        print("Connected successfully to AWS IoT Core!")
        print("Subscribing to neobell/commands")
        # Ensure you have an on_message callback defined and assigned if you subscribe
        # client.on_message = on_message 
        client.subscribe("neobell/commands", qos=1)
    else:
        # Convert rc to string if it's not already (e.g. if it's a ReasonCode object)
        connack_str = mqtt.connack_string(rc) if isinstance(rc, int) else str(rc)
        print(f"Connection failed with result code {rc} ({connack_str})")
        # ... (rest of your error handling in on_connect)


# Adjusted on_disconnect signature
def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    # disconnect_flags: an integer, often 0 for a normal disconnect by client,
    #                 or other values for broker-initiated disconnects.
    # reason_code: a ReasonCode object (from paho.mqtt.reasoncodes) or an integer.
    # properties: an object containing MQTTv5 properties, or None.

    reason_code_value = -1
    reason_string = "Unknown"

    if isinstance(reason_code, int): # Simple integer RC (less common with CallbackAPIVersion.VERSION2 for disconnects)
        reason_code_value = reason_code
        reason_string = mqtt.error_string(reason_code) # Generic error string
    elif hasattr(reason_code, 'value') and hasattr(reason_code, 'getName'): # Likely a Paho ReasonCode object
        reason_code_value = reason_code.value
        reason_string = reason_code.getName() # More specific MQTTv5 reason
    elif reason_code is not None: # Fallback if it's some other object
        reason_string = str(reason_code)


    print(f"Disconnected. Client: {client}, Userdata: {userdata}, Disconnect Flags: {disconnect_flags}, Reason Code Value: {reason_code_value}, Reason: {reason_string}, Properties: {properties}")

    if reason_code_value != 0: # MQTT_RC_SUCCESS (0) usually means a clean disconnect initiated by the client
        print("Unexpected disconnection.")
        # Consider implementing reconnection logic here.

def on_publish(client, userdata, mid, reason_code=None, properties=None): # Adjusted for Paho v2
    # For Paho v2.x, 'rc' is often replaced by a 'reason_code' object and properties
    # The 'mid' is always present.
    # If reason_code is an int and 0, or a ReasonCode object with value 0, it's success.
    publish_successful = False
    if isinstance(reason_code, int) and reason_code == 0:
        publish_successful = True
    elif hasattr(reason_code, 'value') and reason_code.value == 0: # paho.mqtt.reasoncodes.MQTTReasonCode
        publish_successful = True
    
    if publish_successful:
        print(f"Message {mid} published successfully.")
    else:
        reason_str = str(reason_code) if reason_code is not None else "Unknown reason"
        print(f"Message {mid} publish failed. Reason: {reason_str}, Properties: {properties}")


def on_message(client, userdata, msg): # Standard signature for on_message
    print(f"Received message on topic '{msg.topic}': {msg.payload.decode()}")

# --- Setup MQTT Client ---
# Ensure CLIENT_ID is loaded from .env and is a string
if not isinstance(CLIENT_ID, str):
    print(f"Error: CLIENT_ID '{CLIENT_ID}' is not a string. Please check your .env file or environment variables.")
    exit()

try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    print("Paho MQTT Client initialized with CallbackAPIVersion.VERSION2")
except TypeError: # Fallback for older paho-mqtt
    mqtt_client = mqtt.Client(client_id=CLIENT_ID)
    print("Paho MQTT Client initialized (older version, no CallbackAPIVersion)")
except ValueError as ve: # Catch if client_id is not valid (e.g. not a string)
    print(f"Error initializing MQTT Client: {ve}")
    exit()


# ... (tls_set remains the same) ...
mqtt_client.tls_set(
    ca_certs=ROOT_CA_PATH,
    certfile=DEVICE_CERT_PATH,
    keyfile=PRIVATE_KEY_PATH,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLS_CLIENT, # Using PROTOCOL_TLS_CLIENT is generally fine
    ciphers=None
)

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_publish = on_publish
mqtt_client.on_message = on_message # Assign the on_message callback

# --- Connect and Loop ---
# Ensure PORT is an integer
if PORT is None:
    print("Error: PORT environment variable not set.")
    exit()
try:
    mqtt_port = int(PORT)
except ValueError:
    print(f"Error: PORT '{PORT}' is not a valid integer.")
    exit()

try:
    print(f"Attempting to connect to {AWS_IOT_ENDPOINT} on port {mqtt_port}...")
    mqtt_client.connect(AWS_IOT_ENDPOINT, mqtt_port, keepalive=60)
except ssl.SSLError as e:
    print(f"SSL Error during connect: {e}")
    print("Check certificates, private key, Root CA, endpoint, and device date/time.")
    exit()
except Exception as e:
    print(f"Error during connect: {e}")
    exit()

mqtt_client.loop_start()

# --- Example: Publish a message ---
try:
    # It's good practice to wait for connection to be established before publishing
    # You can use a flag set in on_connect or a short sleep, though loop_start should handle it.
    # For robustness, check client.is_connected() before publishing in a real app.
    time.sleep(2) # Give a moment for connection to fully establish and on_connect to fire

    while True: # In a real app, you might not loop forever publishing like this
        if mqtt_client.is_connected(): # Check connection status
            message = f"Hello from Radxa NeoBell at {time.time()}"
            topic = "neobell/status"
            print(f"Publishing to {topic}: {message}")
            result = mqtt_client.publish(topic, message, qos=1)
            
            # Optional: wait_for_publish can be blocking and might hide other issues if used in the main loop
            # It's often better to rely on the on_publish callback for confirmation.
            # For debugging, it's okay:
            try:
                result.wait_for_publish(timeout=5) 
                if not result.is_published(): # Double check after wait
                    reason_str = str(result.rc) if isinstance(result.rc, int) else str(result.rc) # rc can be ReasonCode
                    print(f"Message to {topic} was not published (after wait). Reason: {reason_str}")
            except RuntimeError as re: # wait_for_publish can raise RuntimeError if already disconnected
                print(f"RuntimeError during wait_for_publish: {re}")
            except ValueError as ve: # Can happen if mid is not valid
                print(f"ValueError during wait_for_publish: {ve}")

        else:
            print("Client is not connected. Skipping publish.")
            # Potentially attempt to reconnect here or signal an error
            
        time.sleep(10)
except KeyboardInterrupt:
    print("KeyboardInterrupt received, disconnecting...")
except Exception as e:
    print(f"An error occurred in the main loop: {e}")
finally:
    print("Stopping MQTT loop and disconnecting client.")
    mqtt_client.loop_stop()
    mqtt_client.disconnect() # This should trigger on_disconnect with rc=0 or a clean ReasonCode
    print("Disconnected.")
