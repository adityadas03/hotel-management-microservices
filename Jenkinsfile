pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out Hotel Management project...'
                checkout scm
            }
        }

        stage('Check Docker') {
            steps {
                echo 'Checking Docker installation...'
                bat 'docker --version'
                bat 'docker compose version'
            }
        }

        stage('Build Docker Images') {
            steps {
                echo 'Building Docker images...'
                bat 'docker compose build'
            }
        }

        stage('Stop Old Containers') {
            steps {
                echo 'Stopping existing Hotel Management containers...'
                bat 'docker compose down'
            }
        }

        stage('Start Services') {
            steps {
                echo 'Starting Hotel Management services...'
                bat 'docker compose up -d'
            }
        }

        stage('Check Services') {
            steps {
                echo 'Checking running services...'
                bat 'docker compose ps'
            }
        }

        stage('Test Room Service') {
            steps {
                echo 'Testing Room Service...'
                bat 'curl -f http://localhost:8001/'
            }
        }

        stage('Test Booking Service') {
            steps {
                echo 'Testing Booking Service...'
                bat 'curl -f http://localhost:8002/'
            }
        }

        stage('Test Billing Service') {
            steps {
                echo 'Testing Billing Service...'
                bat 'curl -f http://localhost:8003/'
            }
        }
    }

    post {

        success {
            echo '=========================================='
            echo 'HOTEL MANAGEMENT DEPLOYMENT SUCCESSFUL!'
            echo '=========================================='
        }

        failure {
            echo '=========================================='
            echo 'JENKINS PIPELINE FAILED'
            echo 'Check the Console Output.'
            echo '=========================================='

            bat 'docker compose ps'
        }
    }
}