#!flask/bin/python
import logging
import random

from flask import Flask, jsonify, request, make_response, send_from_directory, \
    g
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__, static_url_path="")
auth = HTTPBasicAuth()



@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

#an auth placeholder
@app.route('/auth')
@auth.login_required
def get_auth_token():
    return jsonify({'token': g.system.generate_auth_token()})


@app.route('/status', methods=['GET'])
def provisioner_status():
    return "Provisioner service version: 0.0\nProvisioner status: Active \n"

@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    if request.method == 'POST':
        if request.headers['Content-Type'] == 'application/octet-stream':
            f = open('./binary', 'wb')
            f.write(request.data)
            f.close()
            return 'JOB-ID:1234\n'
        else:
            return "Incorrect data type\n"
    elif request.method == 'GET':
        return "List of your jobs\nJOB-1234\n"

@app.route('/jobs/<int:job_id>', methods=['GET','PUT'])
def job_info(job_id):
    if request.method == 'GET':
        index = random.randint(0,2)
        status_list = ["QUEUED", "IN_PROGRESS", "COMPLETE"]
        return "JOB-ID: %s\n---------------------\nSTATUS:%s\n" % (job_id, status_list[index])
    if request.method == 'PUT':
        if request.headers['Content-Type'] == 'application/octet-stream':
            f = open('./binary', 'wb')
            f.write(request.data)
            f.close()
            return 'JOB-ID: %s ammended with additional resources\n' % job_id
        else:
            return "Incorrect data type\n"

@app.route('/jobs/<int:job_id>/logs', methods=['GET'])
def get_job_logs(job_id):
    filename = "joblog.txt"
    return send_from_directory(directory="uploads", filename=filename)


@app.route('/jobs/<int:job_id>/teardown', methods=['POST'])
def teardown_job(job_id):
    #content = request.get_json(silent=True)
    #logging.info(content)
    return "Tearing down machines for job: " + str(job_id) + "\n"

@app.route('/jobs/<int:job_id>/nodes/<int:node_id>/teardown', methods=['POST'])
def teardown_node(job_id, node_id):
    #content = request.get_json(silent=True)
    #logging.info(content)
    return "Tearing down machine: " + str(node_id) + ", for job: " + str(job_id) + "\n"

@app.route('/jobs/<int:job_id>/nodes/<int:node_id>', methods=['GET'])
def node_info(job_id, node_id):
    if request.method == 'GET':
        index = random.randint(0,2)
        status_list = ["QUEUED", "IN_PROGRESS", "COMPLETE"]
        return "Node-ID: %s\n---------------------\nSTATUS:%s\n" % (node_id, status_list[index])

@app.route('/jobs/<int:job_id>/nodes/<int:node_id>/logs', methods=['GET'])
def get_node_logs(job_id, node_id):
    filename = "nodelog.txt"
    return send_from_directory(directory="uploads", filename=filename)

@app.route('/jobs/<int:job_id>/output_file', methods=['GET'])
def provision_job_output(job_id):
    uploads = "uploads"
    filename = "provisioner.output.json"
    return send_from_directory(directory=uploads, filename=filename)

@app.route('/jobs/<int:job_id>/nodes/<int:node_id>/output_file', methods=['GET'])
def provision_node_output(job_id, node_id):
    uploads = "uploads"
    filename = "provisioner.output.json"
    return send_from_directory(directory=uploads, filename=filename)


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='provision_service.log',
                    filemode='w')


if __name__ == '__main__':
    app.run(debug=True,
            host='0.0.0.0')

