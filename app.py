from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import io
# import numpy as np
app = Flask(__name__)

# Global variable to hold the CSV content for download
allocation_csv_content = None

@app.route('/')
def upload_page():
    return render_template('upload.html')


def alloting(dfg, dfh):
    """Function to allocate groups to hostel rooms based on gender and capacity."""
    allocation = []
    # Rename columns for clarity
    dfg.columns = ['Group ID','Members','Gender']
    dfh.columns = ['Hostel Name','Room Number','Capacity','Gender']

    # Iterate over each group from the groups dataframe (dfg)
    for _, group in dfg.iterrows():
        group_id = group['Group ID']
        members = group['Members']
        gender = group['Gender']

        # Handle multiple genders in the group
        if '&' in gender:
            genders = gender.split('&')
            gender_count = [int(s.split()[0]) for s in genders]
            gender_type = [s.split()[1] for s in genders]
        else:
            gender_count = [members]
            gender_type = [gender]

        # Allocate members to rooms based on gender and capacity
        for count, g in zip(gender_count, gender_type):
            while count > 0:
                avail_rooms = dfh[(dfh['Gender'] == g) & (dfh['Capacity'] >= count)]
                avail_rooms = avail_rooms.sort_values(by='Capacity')
                
                if not avail_rooms.empty:
                    room = avail_rooms.iloc[0]
                    allocation.append({
                        'Group ID': group_id,
                        'Hostel Name': room['Hostel Name'],
                        'Room Number': room['Room Number'],
                        'Members Allocated': count,
                        'Members remaining': 0,
                        # 'Capacity': room['Capacity']
                    })
                    dfh.at[room.name, 'Capacity'] -= count
                    if dfh.at[room.name, 'Capacity'] == 0:
                        dfh = dfh.drop(room.name)
                    break
                else:
                    avail_rooms = dfh[(dfh['Gender'] == g) & (dfh['Capacity'] <= count)]
                    if not avail_rooms.empty:
                        avail_rooms = avail_rooms.sort_values(by='Capacity', ascending=False)
                        room = avail_rooms.iloc[0]
                        allocation.append({
                            'Group ID': group_id,
                            'Hostel Name': room['Hostel Name'],
                            'Room Number': room['Room Number'],
                            'Members Allocated': room['Capacity'],
                            'Members remaining': 0,
                            # 'Capacity': room['Capacity']
                        })
                        count -= room['Capacity']
                        dfh = dfh.drop(room.name)
                        # count = 0
                    else:
                        # If no suitable room found, mark allocation as NA
                        allocation.append({
                            'Group ID': group_id,
                            'Hostel Name': 'NA',
                            'Room Number': 'NA',
                            'Members Allocated': 0,
                            'Members remaining': count,
                            # 'Capacity': 'NA'
                        })
                        count = 0
    return  allocation

@app.route('/upload', methods=['POST'])
def upload_files():

    """Handle file upload and allocation process."""

    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({"error": "missing files"}), 400
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    try:
        # Read CSV files into pandas DataFrames
        dfg = pd.read_csv(file1)
        dfh = pd.read_csv(file2)
    except Exception as e:
        return jsonify({'Error': str(e)}), e
    
    try:
        # Perform allocation based on uploaded data
        allocation = alloting(dfg, dfh)
        allocation_df = pd.DataFrame(allocation)
        
        #Prepare CSV for download
        output = io.BytesIO()
        allocation_df.to_csv(output, index=False)
        output.seek(0)
        
        allocation_csv_content = output.getvalue()

        # Render result template with allocation data
        return render_template('result.html', allocation_html=allocation_df.to_html(classes='data', header="true", index=False))
    
    except Exception as e:
        # Render error template if allocation process fails
        return render_template('error.html', message=f"Error during allocation: {str(e)}"), 500


@app.route('/download')
def download_file():
    """Download allocated data as CSV."""
    global allocation_csv_content
    return send_file(io.BytesIO(allocation_csv_content),
                     mimetype='text/csv',
                     download_name='allocation.csv',
                     as_attachment=True)

@app.route('/again')
def again():
    """Redirect to upload page to start over."""
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)

