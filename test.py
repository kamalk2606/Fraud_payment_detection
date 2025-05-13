import requests
import json

def predict_fraud(data_string):
    """
    Send data to the fraud detection API and interpret the result.
    
    Args:
        data_string: A string containing the transaction data in CSV format
        
    Returns:
        A tuple containing (raw_probability, is_fraud)
    """
    # API endpoint
    url = "https://aavzy9x555.execute-api.us-east-1.amazonaws.com/PS-2/PS2-API-MODEL"
    
    # Prepare the payload
    payload = {"data": data_string}
    
    # Make the POST request
    response = requests.post(url, json=payload)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response
        response_data = response.json()
        
        # Extract the result (probability)
        result_body = json.loads(response_data.get('body', '{}'))
        probability = float(result_body.get('result', 0))
        
        # Determine if it's fraud based on a threshold
        # Typically, a very low threshold like 0.5 or 0.1 is used for fraud detection
        # since the cost of missing fraud is high
        threshold = 0.5
        is_fraud = 1 if probability >= threshold else 0
        
        return probability, is_fraud
    else:
        print(f"Error: API request failed with status code {response.status_code}")
        return None, None

# Example usage
if __name__ == "__main__":
    # Your test data
    test_data = "278,330218.42,20866.00,351084.42,452419.57,122201.15,0,1,0,0,0,0"
    
    # Get prediction
    probability, is_fraud = predict_fraud(test_data)
    
    if probability is not None:
        print(f"Raw probability score: {probability}")
        print(f"Is fraud (1) or not fraud (0): {is_fraud}")
        
        # The value you received is very small (2.1279122108808224e-07)
        # This suggests the transaction is likely NOT fraud
        if probability < 0.001:
            print("This transaction has a very low probability of being fraudulent.")