resource "aws_subnet" "public" {
  count = length(local.azs)

  vpc_id                  = aws_vpc.main.id
  availability_zone       = local.azs[count.index]
  cidr_block              = local.public_cidrs[count.index]
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.project}-public-${local.az_suffixes[count.index]}"
    Tier = "public"
  }
}

resource "aws_subnet" "app" {
  count = length(local.azs)

  vpc_id            = aws_vpc.main.id
  availability_zone = local.azs[count.index]
  cidr_block        = local.app_cidrs[count.index]

  tags = {
    Name = "${var.project}-app-${local.az_suffixes[count.index]}"
    Tier = "app"
  }
}

resource "aws_subnet" "data" {
  count = length(local.azs)

  vpc_id            = aws_vpc.main.id
  availability_zone = local.azs[count.index]
  cidr_block        = local.data_cidrs[count.index]

  tags = {
    Name = "${var.project}-data-${local.az_suffixes[count.index]}"
    Tier = "data"
  }
}
