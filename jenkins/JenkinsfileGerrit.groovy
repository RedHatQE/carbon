def cloneRepo() {
    checkout([
        $class: 'GitSCM',
        branches: [[name: "${GERRIT_PATCHSET_REVISION}"]],
        doGenerateSubModuleConfigurations: false,
        extensions: [[$class: 'CleanBeforeCheckout']],
        submoduleCfg: [],
        userRemoteConfigs: [[
            credentialsId: '5ed678e3-0a20-46da-979a-4192e7523c33',
            refspec: "${GERRIT_REFSPEC}",
            url: 'ssh://qe-pit-jenkins@code.engineering.redhat.com:22/carbon'
        ]]
    ])
}

pipeline {
    agent { label "${AGENT}" }

    stages {
        stage('clone') {
            steps {
                cleanWs()
                cloneRepo()
            }
        }
        stage('env') {
            steps {
                sh """
                virtualenv venv
                source venv/bin/activate
                pip install tox
                """
            }
        }
        stage('unit tests') {
            steps {
                sh """
                source venv/bin/activate
                make
                """
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
