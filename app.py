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
    allocation = []
    dfg.columns = ['Group ID','Members','Gender']
    dfh.columns = ['Hostel Name','Room Number','Capacity','Gender']
    
    for _, group in dfg.iterrows():
        group_id = group['Group ID']
        members = group['Members']
        gender = group['Gender']

        if '&' in gender:
            genders = gender.split('&')
            gender_count = [int(s.split()[0]) for s in genders]
            gender_type = [s.split()[1] for s in genders]
        else:
            gender_count = [members]
            gender_type = [gender]

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
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({"error": "missing files"}), 400
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    try:
        dfg = pd.read_csv(file1)
        dfh = pd.read_csv(file2)
    except Exception as e:
        return jsonify({'Error': str(e)}), e
    
    allocation = alloting(dfg, dfh)
    allocation_df = pd.DataFrame(allocation)

    output = io.BytesIO()
    allocation_df.to_csv(output, index=False)
    output.seek(0)

    # Convert the dataframes to HTML tables
    # dfg_html = dfg.to_html(classes='data', header="true", index=False)
    # dfh_html = dfh.to_html(classes='data', header="true", index=False)
    allocation_html = allocation_df.to_html(classes='data', header="true", index=False)

    # Save the CSV content in a global variable to allow for download
    global allocation_csv_content
    allocation_csv_content = output.getvalue()

    return render_template('result.html', allocation_html=allocation_html)


@app.route('/download')
def download_file():
    global allocation_csv_content
    return send_file(io.BytesIO(allocation_csv_content),
                     mimetype='text/csv',
                     download_name='allocation.csv',
                     as_attachment=True)

@app.route('/again')
def again():
    return render_template('upload.html')



if __name__ == '__main__':
    app.run(debug=True)

