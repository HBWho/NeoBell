import time
import json
import uuid
import os
import threading
import requests
import logging
from datetime import datetime, timezone
from awscrt.mqtt import QoS
from awsiot import mqtt_connection_builder
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

load_dotenv()

logger = logging.getLogger(__name__)

class AwsIotClient:
    """
    A client to handle all communications with AWS IoT Core and S3,
    encapsulating connection, publishing, and response handling.
    """
    def __init__(self, client_id, endpoint, port, cert_path, key_path, ca_path):
        self.sbc_id = client_id
        self.endpoint = endpoint
        self.port = int(port)
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        
        self.mqtt_connection = None
        self.response_events = {}
        self.received_payloads = {}
        
        # Dynamically build topic maps based on the SBC_ID
        self._build_topic_maps()

    def _build_topic_maps(self):
        """Builds the topic strings using the instance's sbc_id."""
        base_path = f"neobell/sbc/{self.sbc_id}"
        self.topic_map = {
            'visitor_registration': f"{base_path}/registrations/request-upload-url",
            'video_message': f"{base_path}/messages/request-upload-url",
            'permissions_check': f"{base_path}/permissions/request",
            'package_check': f"{base_path}/packages/request",
            'package_status_update': f"{base_path}/packages/status-update/request",
            'log_submission': f"{base_path}/logs/submit",
            'nfc_verify': f"{base_path}/nfc/verify-tag/request",
        }
        self.response_topics = {
            'visitor_registration': f"{base_path}/registrations/upload-url-response",
            'video_message': f"{base_path}/messages/upload-url-response",
            'permissions_check': f"{base_path}/permissions/response",
            'package_check': f"{base_path}/packages/response",
            'package_status_update': f"{base_path}/packages/status-update/response",
            'nfc_verify': f"{base_path}/nfc/verify-tag/response",
        }
        
    # --- Connection Management ---

    def connect(self):
        """Establishes the MQTT connection to AWS IoT Core."""
        if self.mqtt_connection:
            return True
        
        logger.info(f"Attempting to connect to {self.endpoint} with ClientID: {self.sbc_id}")
        try:
            self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
                endpoint=self.endpoint,
                port=self.port,
                cert_filepath=self.cert_path,
                pri_key_filepath=self.key_path,
                ca_filepath=self.ca_path,
                on_connection_interrupted=self._on_connection_interrupted,
                on_connection_resumed=self._on_connection_resumed,
                client_id=self.sbc_id,
                clean_session=True,
                keep_alive_secs=30
            )
            connect_future = self.mqtt_connection.connect()
            connect_future.result(timeout=10.0)
            logger.info("Successfully connected to AWS IoT Core!")
            self._subscribe_to_all_response_topics()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to AWS IoT Core: {e}")
            self.mqtt_connection = None
            return False

    def disconnect(self):
        """Disconnects from AWS IoT Core."""
        if self.mqtt_connection:
            logger.info("Disconnecting from AWS IoT Core...")
            disconnect_future = self.mqtt_connection.disconnect()
            disconnect_future.result(timeout=5.0)
            logger.info("Disconnected.")
            self.mqtt_connection = None

    def __enter__(self):
        """Context manager entry: connects the client."""
        if not self.connect():
            raise RuntimeError("Failed to connect to AWS IoT.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: disconnects the client."""
        self.disconnect()

    # --- Internal Callbacks and Helpers ---

    def _on_connection_interrupted(self, connection, error, **kwargs):
        logger.warning(f"Connection interrupted. Error: {error}")

    def _on_connection_resumed(self, connection, return_code, session_present, **kwargs):
        logger.info(f"Connection resumed. Return Code: {return_code}, Session Present: {session_present}")
        if return_code == connection.RESUME_RECONNECT_SUCCESS and not session_present:
            logger.info("Session not present. Resubscribing to all topics...")
            self._subscribe_to_all_response_topics()

    def _on_message_received(self, topic, payload, **kwargs):
        logger.info(f"Message received on topic '{topic}'")
        try:
            decoded_payload = json.loads(payload.decode('utf-8'))
            self.received_payloads[topic] = decoded_payload
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from topic {topic}. Payload: {payload.decode('utf-8')}")
            self.received_payloads[topic] = {"error": "JSONDecodeError"}
        
        if topic in self.response_events:
            self.response_events[topic].set()

    def _subscribe_to_topic(self, topic, qos=QoS.AT_LEAST_ONCE):
        logger.info(f"Subscribing to topic: {topic}")
        subscribe_future, _ = self.mqtt_connection.subscribe(
            topic=topic, qos=qos, callback=self._on_message_received
        )
        subscribe_result = subscribe_future.result(timeout=5.0)
        logger.info(f"Subscribed to '{topic}' with QoS {subscribe_result['qos']}")
        self.response_events[topic] = threading.Event()

    def _subscribe_to_all_response_topics(self):
        for topic in self.response_topics.values():
            self._subscribe_to_topic(topic)

    def _publish_and_wait(self, action_key, payload_dict, timeout=15.0):
        """Publishes a message and waits for a response on the corresponding topic."""
        request_topic = self.topic_map.get(action_key)
        response_topic = self.response_topics.get(action_key)
        
        if not request_topic or not response_topic:
            logger.error(f"Invalid action key: {action_key}")
            return None

        # Clear previous event and payload for this response topic
        self.response_events[response_topic].clear()
        self.received_payloads.pop(response_topic, None)

        logger.info(f"Publishing to '{request_topic}' for action '{action_key}'")
        try:
            self.mqtt_connection.publish(
                topic=request_topic, payload=json.dumps(payload_dict), qos=QoS.AT_LEAST_ONCE
            )
        except Exception as e:
            logger.error(f"Failed to publish to '{request_topic}': {e}")
            return None

        logger.info(f"Waiting for response on '{response_topic}' for {timeout}s...")
        if self.response_events[response_topic].wait(timeout=timeout):
            logger.info(f"Response received for '{action_key}'.")
            return self.received_payloads.get(response_topic)
        else:
            logger.warning(f"Timeout waiting for response for '{action_key}'.")
            return None

    def _upload_to_s3(self, presigned_url, file_path, metadata, content_type):
        """Uploads a file to S3 using a pre-signed URL."""
        try:
            logger.info(f"Uploading '{file_path}' to S3.")
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            headers = {'Content-Type': content_type}
            if metadata:
                headers.update(metadata)

            response = requests.put(presigned_url, data=file_data, headers=headers)
            response.raise_for_status()
            logger.info("S3 upload successful.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"S3 upload failed: {e.response.text if e.response else e}")
            return False

    # --- Public API Methods (High-Level Business Logic) ---

    def register_visitor(self, image_path, visitor_name, user_id, permission_level):
        """Requests a URL to register a new visitor and uploads their image."""
        logger.info(f"Registering new visitor '{visitor_name}' with permission '{permission_level}'.")
        payload = {
            "face_tag_id": user_id,
            "visitor_name": visitor_name,
            "permission_level": permission_level
        }
        response = self._publish_and_wait('visitor_registration', payload)
        
        if response and "presigned_url" in response:
            if self._upload_to_s3(response["presigned_url"], image_path, response.get("required_metadata_headers"), 'image/jpeg'):
                return user_id
        logger.error("Failed to complete visitor registration.")
        return None

    def send_video_message(self, video_path, visitor_face_tag_id, duration_sec):
        """Requests a URL to send a video message and uploads the video."""
        logger.info(f"Sending video message for visitor '{visitor_face_tag_id}'.")
        payload = {"visitor_face_tag_id": visitor_face_tag_id, "duration_sec": str(duration_sec)}
        response = self._publish_and_wait('video_message', payload)

        if response and "presigned_url" in response:
            return self._upload_to_s3(response["presigned_url"], video_path, response.get("required_metadata_headers"), 'video/mp4')
        logger.error("Failed to get pre-signed URL for video message.")
        return False

    def check_permissions(self, face_tag_id):
        """Checks the permission level for a given face tag ID."""
        logger.info(f"Checking permissions for face_tag_id: {face_tag_id}")
        return self._publish_and_wait('permissions_check', {"face_tag_id": face_tag_id})

    def request_package_info(self, identifier_type, identifier_value):
        """Requests package information using an order_id or tracking_number."""
        logger.info(f"Requesting package info for {identifier_type}: {identifier_value}")
        payload = {"identifier_type": identifier_type, "identifier_value": identifier_value}
        return self._publish_and_wait('package_check', payload)
    
    def update_package_status(self, tracking_number, new_status):
        """Updates the status of a package."""
        logger.info(f"Updating package status for order '{tracking_number}' to '{new_status}'.")
        payload = {"tracking_number": tracking_number, "new_status": new_status}
        return self._publish_and_wait('package_status_update', payload)

    def verify_nfc_tag(self, nfc_id):
        """Verifies an NFC tag against the backend."""
        logger.info(f"Verifying NFC tag: {nfc_id}")
        return self._publish_and_wait('nfc_verify', {"nfc_id_scanned": nfc_id})

    def submit_log(self, event_type, summary, details):
        """Submits a device log entry to AWS. Does not wait for a response."""
        logger.info(f"Submitting log: {summary}")
        payload = {
            "log_timestamp": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
            "event_type": event_type,
            "summary": summary,
            "event_details": details
        }
        request_topic = self.topic_map.get('log_submission')
        try:
            self.mqtt_connection.publish(
                topic=request_topic, payload=json.dumps(payload), qos=QoS.AT_LEAST_ONCE
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish log: {e}")
            return False
