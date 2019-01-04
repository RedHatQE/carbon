def cloneRepo() {
    checkout([
        $class: 'GitSCM',
        branches: [[name: "${GERRIT_PATCHSET_REVISION}"]],
        doGenerateSubModuleConfigurations: false,
        extensions: [[$class: 'CleanBeforeCheckout']],
        submoduleCfg: [],
        userRemoteConfigs: [[
            refspec: "${GERRIT_REFSPEC}",
            url: 'https://code.engineering.redhat.com/gerrit/carbon.git'
        ]]
    ])
}

pipeline {
    agent { label "carbon-slave" }

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
            archiveArtifacts artifacts: 'tests/coverage/**'
        }
    }
}
