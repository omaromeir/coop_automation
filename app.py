from flask import Flask, request, render_template, redirect, url_for, flash
import os
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import plotly.io as pio


app = Flask(__name__)
app.secret_key = 'secret-key'

# Create an upload folder path
UPLOAD_FOLDER = 'uploaded_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SAVED_CSV'] = 'saved_coop_data.csv'  # Path to the saved CSV

# Global DataFrame to store uploaded student data
student_df = pd.DataFrame()

# Helper function to generate timeline data for a student
def generate_timeline_data(row):
    timeline_data = []
    student_name = row['full name']
    start_date = row['co-op start date']

    # Milestones
    coop_plan = start_date
    progress_report_1 = start_date + timedelta(weeks=7)
    progress_report_2 = start_date + timedelta(weeks=14)
    midway_report = start_date + timedelta(weeks=14)  # Midway report coincides with Progress Report 2
    progress_report_3 = start_date + timedelta(weeks=21)
    final_report = start_date + timedelta(weeks=28)

    # Add milestones to the list with student name
    timeline_data.append({'Student': student_name, 'Milestone': 'CO-OP Plan Due', 'Date': coop_plan, 'Task': 'CO-OP Plan'})
    timeline_data.append({'Student': student_name, 'Milestone': 'Progress Report 1', 'Date': progress_report_1, 'Task': 'Progress Report 1'})
    timeline_data.append({'Student': student_name, 'Milestone': 'Progress Report 2', 'Date': progress_report_2, 'Task': 'Progress Report 2'})
    timeline_data.append({'Student': student_name, 'Milestone': 'Midway Report', 'Date': midway_report, 'Task': 'Midway Report'})
    timeline_data.append({'Student': student_name, 'Milestone': 'Progress Report 3', 'Date': progress_report_3, 'Task': 'Progress Report 3'})
    timeline_data.append({'Student': student_name, 'Milestone': 'Final Report', 'Date': final_report, 'Task': 'Final Report'})

    return timeline_data


def create_timeline_plot(timeline_data, advisor_name):
    # Convert to DataFrame
    df_timeline = pd.DataFrame(timeline_data)
    
    # Sort by date
    df_timeline.sort_values(by="Date", inplace=True)
    
    # Create scatter plot with student names
    fig = px.scatter(df_timeline, x="Date", y="Student", color="Task", symbol="Milestone", 
                     text="Milestone", labels={"Date": "Date", "Student": "Student"},
                     title=f"CO-OP Timeline for Advisor: {advisor_name}")
    
    # Add lines connecting the milestones for each student
    fig.update_traces(marker=dict(size=10))
    fig.update_layout(
        xaxis_title="Timeline",
        yaxis_title="Students",
        hovermode="closest",
        showlegend=True
    )

    return pio.to_html(fig, full_html=False)


# Helper function to clean column names
def clean_columns(df):
    # Strip whitespace and lowercase all column names for uniformity
    df.columns = df.columns.str.strip().str.lower()
    return df

# Route for uploading and reading CSV files (for coordinator)
@app.route('/', methods=['GET', 'POST'])
def index():
    global student_df

    if request.method == 'POST':
        if 'save' in request.form:
            # Update the 'COOP Advisor' column with the selected advisor for each student
            for index, row in student_df.iterrows():
                advisor_field = f'advisor_{row["id"]}'  # Create dynamic field names for each student's advisor
                selected_advisor = request.form.get(advisor_field)
                student_df.at[index, 'coop advisor'] = selected_advisor

            # Save the updated DataFrame to a CSV file
            if not student_df.empty:
                student_df.to_csv(app.config['SAVED_CSV'], index=False)
                flash('Data saved successfully.', 'success')
            else:
                flash('No data to save.', 'danger')
            return redirect(url_for('index'))

        # Get the list of advisors entered by the user
        advisors_input = request.form.get('advisors')
        advisors = [advisor.strip() for advisor in advisors_input.split(',')] if advisors_input else []

        # Check if a file is part of the request
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if a file was actually uploaded
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            # Save the file to the upload folder
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # Read and process the CSV file using pandas
            student_df = pd.read_csv(file_path)

            # Ensure the 'COOP Advisor' column exists, and clean the columns
            student_df = clean_columns(student_df)
            if 'coop advisor' not in student_df.columns:
                student_df['coop advisor'] = ''  # Add the column if it doesn't exist

            # Pass the DataFrame and the list of advisors to the template
            return render_template('index.html', df=student_df, advisors=advisors)

        else:
            flash('Please upload a valid CSV file', 'danger')
            return redirect(request.url)
    
    # On GET request, df and advisors are None
    return render_template('index.html', df=None, advisors=None)


# Route for advisors to view their assigned students
# Route for advisors to view their assigned students with timeline
@app.route('/advisor', methods=['GET', 'POST'])
def advisor():
    global student_df

    # Load the saved CSV file if it exists
    if os.path.exists(app.config['SAVED_CSV']):
        student_df = pd.read_csv(app.config['SAVED_CSV'], parse_dates=['co-op start date'], dayfirst=True)
    else:
        flash('No saved data found. Please ensure the coordinator has saved the data.', 'danger')
        return render_template('advisor.html', df=None, timeline_html=None)

    if request.method == 'POST':
        # Get the advisor name from the form
        advisor_name = request.form.get('advisor_name').strip()

        if advisor_name:
            # Filter the DataFrame to show only students assigned to this advisor
            if 'coop advisor' in student_df.columns:
                filtered_df = student_df[student_df['coop advisor'] == advisor_name]

                if filtered_df.empty:
                    flash(f'No students found for advisor: {advisor_name}', 'danger')
                    return render_template('advisor.html', df=None, timeline_html=None)

                # Generate timeline for each student
                timeline_data = []
                for _, row in filtered_df.iterrows():
                    timeline_data += generate_timeline_data(row)

                # Create the timeline plot
                timeline_html = create_timeline_plot(timeline_data, advisor_name)
                return render_template('advisor.html', df=filtered_df, timeline_html=timeline_html)

            else:
                flash('COOP Advisor column not found in the CSV file.', 'danger')
                return render_template('advisor.html', df=None, timeline_html=None)

        else:
            flash('Please enter a valid advisor name.', 'danger')
            return redirect(request.url)

    return render_template('advisor.html', df=None, timeline_html=None)

if __name__ == '__main__':
    app.run(debug=True)
