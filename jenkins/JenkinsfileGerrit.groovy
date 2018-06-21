pipeline {
    agent {
        node {
            label 'carbon'
        }
    }
    stages {
        stage('Clone') {
            steps {
                checkout([
                        $class: 'GitSCM',
                        branches: [[name: "${GERRIT_PATCHSET_REVISION}"]],
                        doGenerateSubmoduleConfigurations: false,
                        extensions: [[$class: 'CleanBeforeCheckout']],
                        submoduleCfg: [],
                        userRemoteConfigs: [[
                                                    credentialsId: '5ed678e3-0a20-46da-979a-4192e7523c33',
                                                    refspec: "${GERRIT_REFSPEC}",
                                                    url: 'ssh://qe-pit-jenkins@code.engineering.redhat.com:22/carbon'
                                            ]]
                ])
            }
        }
        stage('Env Setup') {
            steps {
                sh 'virtualenv venv'
                sh 'source venv/bin/activate'
                sh 'pip install -r test-requirements.txt'
            }
        }
        stage('Validation') {
            parallel {
                stage('Tox Python 2') {
                    steps {
                        dir('carbon') {
                            sh 'tox -e py27'
                        }
                    }
                }
                stage('Tox Python 3') {
                    steps {
                        dir('carbon') {
                            sh 'tox -e py36'
                        }
                    }
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'tests/cover/**'
            junit 'tests/cover/functional/py27/nosetests.xml, tests/cover/functional/py36/nosetests.xml'
        }
    }
}