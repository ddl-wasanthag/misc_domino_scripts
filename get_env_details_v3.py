# A script to list compute environments and ownder details, number of executions, last used
import os
import logging
import csv
from pymongo import MongoClient, errors

# Set up logging
logging.basicConfig(filename='environment_data.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_mongo_client():
    """
    Creates and returns a MongoDB client.
    """
    try:
        user = os.environ.get("MONGODB_USERNAME")
        password = os.environ.get("MONGODB_PASSWORD")
        platform_namespace = 'domino-platform'

        # remove authMechanism='SCRAM-SHA-256' if non admin user is used.
        client = MongoClient(
            'mongodb://mongodb-replicaset.{}.svc.cluster.local:27017'.format(platform_namespace), 
            username=user, 
            password=password, 
            authSource='admin', 
            authMechanism='SCRAM-SHA-256'
        )
        logging.info("Successfully connected to MongoDB.")
        return client

    except errors.PyMongoError as e:
        logging.error("Failed to connect to MongoDB: %s", e)
        raise

def get_environment_data(result_limit=500):
    """
    Retrieves environment data with run counts, user, and project information,
    including starting user details.
    """
    try:
        client = get_mongo_client()

        # Select the database and collections
        db = client['domino']
        environments_v2 = db['environments_v2']

        # Perform the aggregation query
        cursor = environments_v2.aggregate([
            {'$match': {'isArchived': False}},
            {'$lookup': {
                'from': 'runs',
                'let': {'environmentId': '$_id'},
                'pipeline': [
                    {'$match': {'$expr': {'$eq': ['$environmentId', '$$environmentId']}}},
                    {'$group': {
                        '_id': '$environmentId',
                        'runsCount': {'$sum': 1},
                        'latestStarted': {'$max': '$started'},
                        'startingUserId': {'$first': '$startingUserId'}  # Get the starting user ID
                    }}
                ],
                'as': 'runData'
            }},
            {'$addFields': {
                'runsCount': {'$ifNull': [{'$arrayElemAt': ['$runData.runsCount', 0]}, 0]},
                'latestStarted': {'$arrayElemAt': ['$runData.latestStarted', 0]},
                'startingUserId': {'$arrayElemAt': ['$runData.startingUserId', 0]}
            }},
            {'$lookup': {
                'from': 'users',
                'localField': 'ownerId',
                'foreignField': '_id',
                'as': 'ownerDetails'
            }},
            {'$unwind': {
                'path': '$ownerDetails',
                'preserveNullAndEmptyArrays': True
            }},
            {'$lookup': {
                'from': 'users',
                'localField': 'startingUserId',
                'foreignField': '_id',
                'as': 'startingUserDetails'
            }},
            {'$unwind': {
                'path': '$startingUserDetails',
                'preserveNullAndEmptyArrays': True
            }},
            {'$addFields': {
                'ownerFullName': '$ownerDetails.fullName',
                'ownerEmail': '$ownerDetails.email',
                'ownerLoginId': '$ownerDetails.loginId.id',
                'startingUserName': '$startingUserDetails.fullName',
                'startingUserEmail': '$startingUserDetails.email',
                'startingUserLoginId': '$startingUserDetails.loginId.id'
            }},
            {'$project': {
                '_id': 0,  # Exclude _id from the output
                'name': 1,
                'description': 1,
                'visibility': 1,
                'isArchived': 1,
                'runsCount': 1,
                'ownerId': 1,
                'latestStarted': 1,
                'ownerFullName': 1,
                'ownerEmail': 1,
                'ownerLoginId': 1,
                'startingUserName': 1,
                'startingUserEmail': 1,
                'startingUserLoginId': 1
            }},
            {'$sort': {'runsCount': -1}}
        ])

        # Limit the results to the specified number
        results = list(cursor)[:result_limit]
        logging.info("Successfully retrieved %d documents.", len(results))
        return results

    except errors.PyMongoError as e:
        logging.error("A PyMongo error occurred: %s", e)
        raise
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)
        raise

def write_to_csv(data, filename='environment_data.csv'):
    """
    Writes the retrieved environment data to a CSV file.
    """
    try:
        with open(filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=[
                'name', 'description', 'visibility', 'isArchived', 'runsCount', 'ownerId',
                'ownerFullName', 'ownerEmail', 'ownerLoginId',
                'latestStarted',
                'startingUserName', 'startingUserEmail', 'startingUserLoginId'
            ])
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        logging.info("Data successfully written to %s.", filename)

    except IOError as e:
        logging.error("Failed to write data to CSV file: %s", e)
        raise

def main():
    try:
        result_limit = 500  # Set the result limit as a variable
        data = get_environment_data(result_limit=result_limit)
        write_to_csv(data)
        logging.info("Script completed successfully.")

    except Exception as e:
        logging.error("Script failed with an error: %s", e)

if __name__ == "__main__":
    main()
