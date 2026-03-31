import boto3

# Document
documentName = "/home/aayesha/Workshop/AWS_Translate/Sample_Doc.jpeg"

# Amazon Textract client
textract = boto3.client('textract')

# Call Amazon Textract
with open(documentName, "rb") as document:
    response = textract.detect_document_text(
        Document={
            'Bytes': document.read(),
        }
    )

#print(response)

# Amazon Translate client
translate = boto3.client('translate')

print ('')
for item in response["Blocks"]:
    if item["BlockType"] == "LINE":
        print ('\033[94m' +  item["Text"] + '\033[0m')
        result = translate.translate_text(Text=item["Text"], SourceLanguageCode="en", TargetLanguageCode="hi")
        print ('\033[92m' + result.get('TranslatedText') + '\033[0m')
