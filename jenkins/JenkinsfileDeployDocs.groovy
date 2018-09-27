def cloneRepo() {
    checkout([
        $class: 'GitSCM',
        branches: [[name: "${BRANCH}"]],
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
                cleanWS()
                cloneRepo()
            }
        }
        stage('setup') {
            steps {
                sh """
                virtualenv venv
                source venv/bin/activate
                pip install -r test-requirements.txt
                pip freeze
                """
            }
        }
        stage('build') {
            steps {
                sh """
                source venv/bin/activate
                make docs
                """
            }
        }
        stage('deploy') {
            sh "sudo rm -rf /var/www/html/*"
            sh "sudo mv docs/_build/html/* /var/www/html/"
            sh "sudo semanage fcontext -a -t httpd_sys_content_t '/var/www/html(/.*)?'"
            sh "sudo restorecon -R /var/www/html"
        }
    }
}