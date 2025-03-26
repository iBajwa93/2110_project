import json
import boto3
import base64

# S3 stuff
S3_BUCKET_NAME = "000350034-dog-breed-detector"
BREED_FACTS_FILE = "dog_breed_facts.json"

# clients
rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

# Load breed facts of JSON  file from S3
def load_breed_facts():
    obj = s3.get_object(Bucket=S3_BUCKET_NAME, Key=BREED_FACTS_FILE)
    data = obj['Body'].read()
    return json.loads(data)

# Load facts and keywords once when the Lambda container has started
BREED_FACTS = load_breed_facts()
BREED_KEYWORDS = [breed.lower() for breed in BREED_FACTS.keys()]

def lambda_handler(event, context):
    try:
        # load the json body which will use Rekognition's built-in api to filter whatever json breeds I wrote down
        body = json.loads(event['body'])

        # Decode image
        image_data = base64.b64decode(body['image'])

        # Call Rekognition to detect labels
        response = rekognition.detect_labels(
            Image={'Bytes': image_data},
            MaxLabels=15,
            MinConfidence=50
        )

        # Filter any detected breeds
        detected_breeds = [
            {
                "breed": label['Name'],
                "confidence": round(label['Confidence'], 2),
                "fun_fact": BREED_FACTS.get(label['Name'], "No fact available.")
            }
            for label in response['Labels']
            if label['Confidence'] >= 50 and label['Name'].lower() in BREED_KEYWORDS
        ]

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps({
                "detected_breeds": detected_breeds or "No recognized breeds found."
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps({"error": str(e)})
        }
