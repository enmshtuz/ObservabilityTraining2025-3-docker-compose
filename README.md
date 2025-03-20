# ObservabilityTraining2025-3-docker-compose

## Project Description
This project defines a simple Python CRUD service for a PostgreSQL database. It uses Docker Compose to set up the database and the service.

## Prerequisites
- Docker

## Usage

### Build and Start the Containers
Run the following command to build and start the containers:
```
docker-compose up --build
```

### CRUD Endpoints
The service exposes the following endpoints:

#### Add Item
```
POST /add/<item_name>
```
Adds a new item to the database.

#### Get All Items
```
GET /get-all
```
Retrieves all items from the database.

#### Get Item by ID
```
GET /get/<item_id>
```
Fetches a specific item by ID.

#### Update Item by ID
```
PUT /update/<item_id>
```
Updates the item with a new name. Pass the new name in the request body.

#### Delete Item by ID
```
DELETE /delete/<item_id>
```
Deletes the item with the specified ID.

### Health Check Endpoints
- **Liveness Probe:** `GET /health` - Returns "Healthy" if the service is running.
- **Readiness Probe:** `GET /ready` - Checks database connectivity and returns "Ready" if the connection is successful.

## Example Usage
To add a new item:
```
curl -X POST http://localhost:5050/add/fake-name
```
To get all items:
```
curl http://localhost:5050/get-all
```
To get a specific items:
```
curl http://localhost:5050/get/1
```
To update an item:
```
curl -X PUT http://localhost:5050/update/1 -d "new-name"
```
To delete an item:
```
curl -X DELETE http://localhost:5050/delete/1
```

