.PHONY: bootstrap plan apply

bootstrap:
	cd bootstrap && terraform init && terraform apply

plan:
	cd envs/dev && terraform init && terraform plan

apply:
	cd envs/dev && terraform init && terraform apply
