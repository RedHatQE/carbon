def cloneRepo() {
    checkout([
            $class: 'GitSCM',
            branches: [[name: "${GERRIT_BRANCH}"]],
            doGenerateSubModuleConfigurations: false,
            extensions: [[$class: 'CleanBeforeCheckout']],
            submoduleCfg: [],
            userRemoteConfigs: [[
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
        stage('sanitize') {
            steps {
                dir('docs') {
                    sh """
                    python wiki-sanitizer.py
                    """
                }
            }
        }
        stage('publish') {
            steps {
                script {
                    def conf_spaces = ['~ccit', 'CentralCI']
                    def conf_parent_pages = ['Carbon Documentation - Development', 'Carbon']

                    CONF_SPACE_NAME=''
                    CONF_PARENT_PAGE=''

                    if (env.GERRIT_BRANCH != 'master') {

                        CONF_SPACE_NAME = conf_spaces[0]
                        CONF_PARENT_PAGE = conf_parent_pages[0]
                    }
                    else {
                        CONF_SPACE_NAME = conf_spaces[1]
                        CONF_PARENT_PAGE = conf_parent_pages[1]
                    }

                    withEnv(["CONF_SPACE_NAME=${CONF_SPACE_NAME}", "CONF_PARENT_PAGE=${CONF_PARENT_PAGE}"]) {
                        withCredentials([usernamePassword(credentialsId: 'f6e65ad2-761a-472f-b45e-e8765d0ad1a1',
                                usernameVariable: 'CONF_SERVER_USER',
                                passwordVariable: 'CONF_SERVER_PASS')]){
                            
                            sh """
                            source venv/bin/activate
                            make docs-wiki
                            """
                        }
                    }
                }
            }
        }
    }
}
