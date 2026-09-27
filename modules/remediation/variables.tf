variable "project" {
  type = string
}

variable "alert_email" {
  type    = string
  default = ""
}

variable "trigger_rules" {
  description = "EventBridge rules that should invoke this function, keyed by a short name (e.g. api_writes). Each one gets an event target and a matching lambda:InvokeFunction permission."
  type = map(object({
    name = string
    arn  = string
  }))
  default = {}
}
