# Serverless DB Query

Wow, this took a long time. All I wanted to do was have an API Gateway that forwarded a request to a Lambda that queried an RDS instance. Was that so much to ask?! I guess not, because it worked. But it wasn't easy I tell you! Here are the steps I had to go through starting from a brand new AWS Account.

# Networking

I'm in the Pacific Northwest in the US, so I chose the Oregon region: us-west-2.

I made a "dev" VPC with `10.0.0.0/16` IPv4 CIDR block based on [this article](https://medium.com/aws-activate-startup-blog/practical-vpc-design-8412e1a18dcc#.bmeh8m3si).

I created an Internet Gateway (`dev-igw`) and a Route Table (`dev-route-table`) in the dev VPC. I added two routes to the route table:

```
0.0.0.0/0 - igw-{randomchars}
::/0 - igw-{randomchars}
```

I subdivided the VPC amongst 4 subnets (one for each availability zone):

```
dev-us-west-2a - 10.0.0.0/18
dev-us-west-2b - 10.0.64.0/18
dev-us-west-2c - 10.0.128.0/18
dev-us-west-2d - 10.0.192.0/18
```

And assigned the Route Table to the first three, leaving the 4th (`dev-us-west-2d`) for something else.

I created two Security Groups:

1) A generic group for talking to EC2 instances (HTTP and SSHing)
2) A group for my RDS Postgres instance (which communicates over TCP)

These could have been one Security Group but whatever.

*Generic Security Group*

Inbound

```
HTTP - TCP - 80 - 0.0.0.0/0
HTTP - TCP - 80 - ::/0
SSH - TCP - 22 - 0.0.0.0/0
SSH - TCP - 22 - ::/0
```

Outbound

```
All traffic - All - All - 0.0.0.0/0
```

*Postgres Group*

Inbound

```
PostgreSQL - TCP - 5432 - 0.0.0.0/0
PostgreSQL - TCP - 5432 - ::/0
```

Outbound

```
PostgreSQL - TCP - 5432 - 0.0.0.0/0
PostgreSQL - TCP - 5432 - ::/0
```

I think that's it?

Another useful article: [https://medium.com/@chamikakasun/an-aws-rds-db-instance-in-a-vpc-accessed-by-an-aws-ec2-instance-in-the-same-vpc-befa659b3dd8](Creating a VPC with Private and Public Subnets and access RDS from EC2 in the same VPC.).


# RDS

I created a free-tier RDS Postgres instance. When you're configuring your instance, be sure to put it in the VPC you created. Toggle open the `"Additional connectivity configuration"` window, then make it "Publicly accessible", choose the "Postgres Security Group" you created, then choose an Availability Zone (I chose "us-west-2a").

If you want to just mess around, you can open the final window: `"Additional Information"`. Turn off all the stuffs.

# Lambda

This was the tough part for me, but it should be easy for you.

I wrote my function in Python, and I wanted to use `psycopg2` to talk to postgres. `psycopg2` is not provided by lambda, so we need to bundle it with the zip you upload to lambda. I'm gonna pretend you're like me on a late Friday night saying "I DON'T CARE JUST LET ME QUERY MY RDS INSTANCE FROM LABMDA FFFFFFFFFFFFF" so just copy the code and move on. Inspect it at your leisure.

The only think _you_ need to do is create the Lambda function. Click "Create Function", give it a name, choose your runtime (I did Python 3.7), and click create.

There's a section I need to add about creating a sufficient IAM role that will allow your Lambda to create CloudwatchLogs. For simplicity, I think it will do it for you. Just do that unless you wanna deal with that.

Another painpoint was the fact that the response from the Lambda function needs to be _exactly_ what is expected and defined in API Gateway. So let's do that.

I used this repo for `psycopg2`: [Repo Link](https://github.com/jkehler/awslambda-psycopg2).

# API Gateway

I wanted my API to look like this: `/is_valid/{hash}`. It checks if a hash is valid. :0

Create a new REST API. Name it something (`is_hash_valid` is probably fine).

In the "Resources" tab, click "Actions" and "Create Resource". Name it `is_valid`. This should set the "Resource Path" to `is_valid`. With the `is_valid` Resource selected, click "Actions" and "Create Resource". Name it `{hash}` and set the "Resource Path" to `{hash}`.

On the `{hash}` resource, click "Actions" and "Create Method", then choose "GET". The "Integration type" will be "Lambda Function" and enable "Use Lambda Proxy integration". Then choose your lambda by typing it into the box.

Now you need to change the return type to match the Lambda return type.

Click on the "Models" tab. Create a new Model with the following Model Schema:

```
{
  "$schema" : "http://json-schema.org/draft-04/schema#",
  "title" : "Hash Valid Schema",
  "type" : "object",
  "properties" : {
    "valid" : { "type" : "boolean" }
  }
}
```

This should match the Lambda code.

The final step is to "deploy" the API. Create a `"dev"` stage by clicking on the "Stages" tab and clicking "Create". Then, pop back over to the "Resources" tab, and click "Actions" then "Deploy API". Choose your stage.

# Deploying

Deploying manually is easy. Just zip up the lambda stuff, then, in the Lambda Console, click your Lambda, then instead of "Edit code inline" for your "Code entry type", choose "Upload a .zip file". Hit "Save". Blamo.

Automation can come later...
