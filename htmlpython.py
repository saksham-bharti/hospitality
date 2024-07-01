from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import io

app = Flask(__name__)

def group_csv(file):
    df1 = pd.read_csv(file)
    return df1

def hostel_csv(file):
    df2 = pd.read_csv(file)
    return df2

def alloting(groups, hostels):
    allocations = []
    
    groups = groups.sort_values(by='Members', ascending=False)

    for index, group in groups.iterrows():
        allocated = False

        for h_index, hostel in hostels.iterrows():
            if group['Gender'].lower() in hostel['Gender'].lower() and group['Members'] <= hostel['Capacity']:
                allocations.append({
                    'Group ID': group['Group ID'],
                    'Hostel Name': hostel['Hostel Name'],
                    'Room Number': hostel['Room Number'],
                    'Members Allocated': group['Members']
                })
                hostels.at[h_index, 'Capacity'] -= group['Members']
                allocated = True
                break
        
        if not allocated:
            allocations.append({
                'Group ID': group['Group ID'],
                'Hostel Name': 'Not Allocated',
                'Room Number': 'N/A',
                'Members Allocated': 0
            })
    return allocations 

@app.route('/')
def upload_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hospitality Process Digitalization</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .container {
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                width: 80%;
                max-width: 600px;
                text-align: center;
            }
            h1 {
                margin-bottom: 20px;
                color: #333;
            }
            form {
                margin-bottom: 20px;
            }
            input[type="file"] {
                margin-bottom: 10px;
            }
            button {
                background-color: #007BFF;
                color: #fff;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #0056b3;
            }
            #results {
                margin-top: 20px;
                text-align: left;
            }
            .result-item {
                background-color: #f9f9f9;
                margin-bottom: 10px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .result-item p {
                margin: 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Upload Group and Hostel Information</h1>
            <form id="upload-form" enctype="multipart/form-data">
                <input type="file" id="group-file" name="group_file" required><br><br>
                <input type="file" id="hostel-file" name="hostel_file" required><br><br>
                <button type="submit">Upload and Allocate</button>
            </form>
            <div id="results"></div>
        </div>
        <script>
            document.getElementById('upload-form').addEventListener('submit', async function(event) {
                event.preventDefault();
                const formData = new FormData();
                formData.append('group_file', document.getElementById('group-file').files[0]);
                formData.append('hostel_file', document.getElementById('hostel-file').files[0]);
                
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                let resultDiv = document.getElementById('results');
                resultDiv.innerHTML = '<h2>Allocation Results</h2>';
                data.forEach(allocation => {
                    const resultItem = document.createElement('div');
                    resultItem.className = 'result-item';
                    resultItem.innerHTML = `
                        <p><strong>Group ID:</strong> ${allocation['Group ID']}</p>
                        <p><strong>Hostel Name:</strong> ${allocation['Hostel Name']}</p>
                        <p><strong>Room Number:</strong> ${allocation['Room Number']}</p>
                        <p><strong>Members Allocated:</strong> ${allocation['Members Allocated']}</p>
                    `;
                    resultDiv.appendChild(resultItem);
                });
            });
        </script>
    </body>
    </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'group_file' not in request.files or 'hostel_file' not in request.files:
        return jsonify({'error': 'Missing files'}), 400

    group_file = request.files['group_file']
    hostel_file = request.files['hostel_file']
    
    try:
        groups = group_csv(io.StringIO(group_file.stream.read().decode('UTF8'), newline=None))
        hostels = hostel_csv(io.StringIO(hostel_file.stream.read().decode('UTF8'), newline=None))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    allocations = alloting(groups, hostels)

    return jsonify(allocations)

if __name__ == '__main__':
    app.run(debug=True)
