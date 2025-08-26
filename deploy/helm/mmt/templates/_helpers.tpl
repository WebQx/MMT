{{- define "mmt.name" -}}
{{- .Chart.Name -}}
{{- end -}}

{{- define "mmt.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
