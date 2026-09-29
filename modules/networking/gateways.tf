resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project}-igw"
  }
}

resource "aws_eip" "nat" {
  count = length(local.azs)

  domain = "vpc"

  tags = {
    Name = "${var.project}-nat-${local.az_suffixes[count.index]}"
  }

  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  count = length(local.azs)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "${var.project}-nat-${local.az_suffixes[count.index]}"
  }

  depends_on = [aws_internet_gateway.main]
}
