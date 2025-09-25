#!/usr/bin/env python3
"""
ArchBuilder.AI Test Data Generator
Generates realistic test data for staging environment
"""

import os
import sys
import asyncio
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from faker import Faker
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Initialize Faker
fake = Faker()

class TestDataGenerator:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://archbuilder:password@localhost:5432/archbuilder_staging')
        self.api_url = os.getenv('API_URL', 'http://localhost:8000')
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)
        
    async def generate_users(self, count: int = 100) -> List[Dict[str, Any]]:
        """Generate test users"""
        print(f"Generating {count} test users...")
        
        users = []
        for i in range(count):
            user = {
                'id': f'user_{i+1:04d}',
                'email': fake.email(),
                'username': fake.user_name(),
                'first_name': fake.first_name(),
                'last_name': fake.last_name(),
                'company': fake.company(),
                'role': random.choice(['architect', 'engineer', 'designer', 'manager']),
                'subscription_tier': random.choice(['free', 'professional', 'enterprise']),
                'created_at': fake.date_time_between(start_date='-1y', end_date='now'),
                'is_active': random.choice([True, True, True, False]),  # 75% active
                'region': random.choice(['us', 'eu', 'asia', 'middle_east']),
                'language': random.choice(['en', 'tr', 'de', 'fr', 'es'])
            }
            users.append(user)
            
        return users
    
    async def generate_projects(self, users: List[Dict], count: int = 200) -> List[Dict[str, Any]]:
        """Generate test projects"""
        print(f"Generating {count} test projects...")
        
        projects = []
        for i in range(count):
            user = random.choice(users)
            project = {
                'id': f'proj_{i+1:04d}',
                'user_id': user['id'],
                'name': f"{fake.word().title()} {random.choice(['Building', 'Complex', 'Tower', 'Center', 'Plaza'])}",
                'description': fake.text(max_nb_chars=200),
                'building_type': random.choice(['residential', 'office', 'retail', 'industrial', 'mixed_use']),
                'total_area_m2': random.randint(500, 50000),
                'floor_count': random.randint(1, 50),
                'status': random.choice(['draft', 'in_progress', 'review', 'completed', 'archived']),
                'created_at': fake.date_time_between(start_date='-1y', end_date='now'),
                'updated_at': fake.date_time_between(start_date='-6m', end_date='now'),
                'region': user['region'],
                'compliance_requirements': random.choice(['basic', 'advanced', 'enterprise']),
                'ai_usage_count': random.randint(0, 100),
                'last_ai_activity': fake.date_time_between(start_date='-1m', end_date='now') if random.random() > 0.3 else None
            }
            projects.append(project)
            
        return projects
    
    async def generate_ai_commands(self, users: List[Dict], projects: List[Dict], count: int = 1000) -> List[Dict[str, Any]]:
        """Generate test AI commands"""
        print(f"Generating {count} test AI commands...")
        
        commands = []
        prompt_templates = [
            "Create a {building_type} layout with {room_count} rooms",
            "Design a {building_type} with {area} square meters",
            "Generate a floor plan for a {building_type} project",
            "Create an energy-efficient {building_type} design",
            "Design a {building_type} with accessibility features",
            "Generate a {building_type} layout optimized for {region} climate"
        ]
        
        for i in range(count):
            user = random.choice(users)
            project = random.choice(projects)
            
            prompt_template = random.choice(prompt_templates)
            prompt = prompt_template.format(
                building_type=project['building_type'],
                room_count=random.randint(3, 20),
                area=project['total_area_m2'],
                region=user['region']
            )
            
            command = {
                'id': f'cmd_{i+1:06d}',
                'user_id': user['id'],
                'project_id': project['id'],
                'prompt': prompt,
                'ai_model': random.choice(['gpt-4', 'claude-3-5-sonnet', 'gemini-pro']),
                'status': random.choice(['pending', 'processing', 'completed', 'failed', 'requires_review']),
                'confidence_score': round(random.uniform(0.6, 0.95), 2),
                'processing_time_seconds': random.randint(5, 120),
                'created_at': fake.date_time_between(start_date='-6m', end_date='now'),
                'completed_at': fake.date_time_between(start_date='-6m', end_date='now') if random.random() > 0.1 else None,
                'requires_human_review': random.choice([True, False, False, False]),  # 25% require review
                'error_message': fake.sentence() if random.random() < 0.05 else None,
                'region': user['region'],
                'subscription_tier': user['subscription_tier']
            }
            commands.append(command)
            
        return commands
    
    async def generate_documents(self, count: int = 500) -> List[Dict[str, Any]]:
        """Generate test documents"""
        print(f"Generating {count} test documents...")
        
        documents = []
        document_types = ['building_code', 'regulation', 'standard', 'reference', 'template']
        
        for i in range(count):
            doc_type = random.choice(document_types)
            document = {
                'id': f'doc_{i+1:04d}',
                'filename': f"{fake.word()}_{doc_type}_{random.randint(1, 100)}.pdf",
                'title': f"{fake.sentence(nb_words=4).title()} {doc_type.title()}",
                'document_type': doc_type,
                'file_size_bytes': random.randint(100000, 10000000),
                'uploaded_at': fake.date_time_between(start_date='-1y', end_date='now'),
                'processed_at': fake.date_time_between(start_date='-1y', end_date='now') if random.random() > 0.1 else None,
                'status': random.choice(['uploaded', 'processing', 'processed', 'failed']),
                'region': random.choice(['us', 'eu', 'asia', 'middle_east']),
                'language': random.choice(['en', 'tr', 'de', 'fr', 'es']),
                'access_count': random.randint(0, 50),
                'last_accessed': fake.date_time_between(start_date='-1m', end_date='now') if random.random() > 0.5 else None
            }
            documents.append(document)
            
        return documents
    
    async def generate_usage_metrics(self, users: List[Dict], commands: List[Dict]) -> List[Dict[str, Any]]:
        """Generate usage metrics"""
        print("Generating usage metrics...")
        
        metrics = []
        for user in users:
            user_commands = [cmd for cmd in commands if cmd['user_id'] == user['id']]
            
            metric = {
                'user_id': user['id'],
                'date': fake.date_between(start_date='-30d', end_date='now'),
                'ai_commands_count': len(user_commands),
                'successful_commands': len([cmd for cmd in user_commands if cmd['status'] == 'completed']),
                'failed_commands': len([cmd for cmd in user_commands if cmd['status'] == 'failed']),
                'total_processing_time': sum(cmd.get('processing_time_seconds', 0) for cmd in user_commands),
                'average_confidence': round(sum(cmd['confidence_score'] for cmd in user_commands) / len(user_commands), 2) if user_commands else 0,
                'subscription_tier': user['subscription_tier'],
                'region': user['region']
            }
            metrics.append(metric)
            
        return metrics
    
    async def insert_data_to_database(self, data: List[Dict], table_name: str):
        """Insert data into database"""
        print(f"Inserting {len(data)} records into {table_name}...")
        
        session = self.Session()
        try:
            for record in data:
                # Convert datetime objects to strings for JSON serialization
                for key, value in record.items():
                    if isinstance(value, datetime):
                        record[key] = value.isoformat()
                
                # Insert record
                insert_sql = f"""
                INSERT INTO {table_name} ({', '.join(record.keys())})
                VALUES ({', '.join([':' + key for key in record.keys()])})
                ON CONFLICT (id) DO NOTHING
                """
                session.execute(text(insert_sql), record)
            
            session.commit()
            print(f"Successfully inserted {len(data)} records into {table_name}")
            
        except Exception as e:
            print(f"Error inserting data into {table_name}: {e}")
            session.rollback()
        finally:
            session.close()
    
    async def send_test_api_requests(self, commands: List[Dict]):
        """Send test API requests to staging environment"""
        print("Sending test API requests...")
        
        for i, command in enumerate(commands[:10]):  # Send first 10 commands
            try:
                payload = {
                    'prompt': command['prompt'],
                    'user_id': command['user_id'],
                    'project_id': command['project_id'],
                    'ai_model': command['ai_model']
                }
                
                response = requests.post(
                    f"{self.api_url}/v1/ai/commands",
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    print(f"✓ API request {i+1} successful")
                else:
                    print(f"✗ API request {i+1} failed: {response.status_code}")
                    
            except Exception as e:
                print(f"✗ API request {i+1} error: {e}")
    
    async def generate_all_data(self):
        """Generate all test data"""
        print("Starting test data generation for ArchBuilder.AI staging environment...")
        
        # Generate base data
        users = await self.generate_users(100)
        projects = await self.generate_projects(users, 200)
        commands = await self.generate_ai_commands(users, projects, 1000)
        documents = await self.generate_documents(500)
        metrics = await self.generate_usage_metrics(users, commands)
        
        # Insert into database
        await self.insert_data_to_database(users, 'users')
        await self.insert_data_to_database(projects, 'projects')
        await self.insert_data_to_database(commands, 'ai_commands')
        await self.insert_data_to_database(documents, 'documents')
        await self.insert_data_to_database(metrics, 'usage_metrics')
        
        # Send test API requests
        await self.send_test_api_requests(commands)
        
        print("Test data generation completed!")
        print(f"Generated:")
        print(f"  - {len(users)} users")
        print(f"  - {len(projects)} projects")
        print(f"  - {len(commands)} AI commands")
        print(f"  - {len(documents)} documents")
        print(f"  - {len(metrics)} usage metrics")

async def main():
    generator = TestDataGenerator()
    await generator.generate_all_data()

if __name__ == "__main__":
    asyncio.run(main())
