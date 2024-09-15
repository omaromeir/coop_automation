import pandas as pd

# Function to read the CSV file
def read_student_data(csv_file_path):
    try:
        # Read the CSV file into a pandas DataFrame
        df = pd.read_csv(csv_file_path)

        # Print the DataFrame to verify contents
        print(df)

        # Optionally, process the data
        for index, row in df.iterrows():
            student_id = row['ID']
            student_name = row['Full name']
            major = row['Major']
            coop_advisor = row['COOP Advisor']
            coop_start = row['CO-OP start date']
            coop_end = row['CO-OP end date']

            # Print each student data row for now
            print(f"Student ID: {student_id}, Name: {student_name}, Major: {major}, Advisor: {coop_advisor}, Start: {coop_start}, End: {coop_end}")

    except Exception as e:
        print(f"Error reading CSV file: {e}")

# Test the function
csv_file_path = '/Users/omaromeir/Documents/GitHub/coop_automation/data/test.csv'  # Replace this with your actual file path
read_student_data(csv_file_path)