#!/bin/bash
clear
echo "Input the json file of key-value pair for input parameter:"
#read jsonFileName
jsonFileName="test.json"
echo $jsonFileName

yamlFileName="submit.yaml"
firstURL="http://localhost:53967/api/v1/workflows/argo-workflows/submit"
secondURL="http://localhost:53967/api/v1/workflows/argo-workflows/"
quote="\""
comma=","
jsonContent=""
yamlContent=""
bracket="}"
counter=0

while read -r line; do
if [[ $line == "{" ]]; then
	continue
fi
	line=${line/{/}
	line=${line//\"/}
	line=${line//\,/}
	line=${line//\ /}
	line=${line/:/=}
	line="$quote$line"
	line="$line$quote"
	line="$line$comma"
	#echo $line
	jsonContent="$jsonContent$line"
done <$jsonFileName
	
# remove last charater	
jsonContent=${jsonContent%?}

echo -e "\n"

while read line; do
	yamlContent="$yamlContent$line"
done <$yamlFileName

yamlContent="${yamlContent/PlaceHolder/$jsonContent}"
yamlContent="$yamlContent$bracket"

# dynamically extract the metadata.name (argo workflow name) of the json response 
templateName=$(curl -s -d "$yamlContent" -H "Content-Type: application/json" -X POST $firstURL | jq '.metadata.name')
templateName=${templateName//\"/}

secondURL="$secondURL$templateName"

#Printing intial results of GET curl request : Failed / Succeeded / Running
result=$(curl -s -X GET $secondURL | jq '.metadata.labels."workflows.argoproj.io/phase"')
result=${result//\"/}
echo $result

#Going to check the variable $result : the status (Failed / Succeeded / Running) of the argowork flow
#Keep pulling the GET curl request
while [ $result == "Running" ]
do
	result=$(curl -s -X GET $secondURL | jq '.metadata.labels."workflows.argoproj.io/phase"')
	result=${result//\"/}
done

echo $result
