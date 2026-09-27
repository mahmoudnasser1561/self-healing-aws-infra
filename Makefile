.PHONY: bootstrap plan apply chaos-s3 chaos-sg chaos-rds chaos-ec2 chaos-ct

bootstrap:
	cd bootstrap && terraform init && terraform apply

plan:
	cd envs/dev && terraform init && terraform plan

apply:
	cd envs/dev && terraform init && terraform apply

chaos-s3:
	./chaos/break-s3-1.sh

chaos-sg:
	./chaos/break-sg-1.sh

chaos-rds:
	./chaos/break-rds-1.sh

chaos-ec2:
	./chaos/break-ec2-1.sh

chaos-ct:
	./chaos/break-ct-1.sh
