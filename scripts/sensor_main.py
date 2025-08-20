import csv
import json
import re
import socket
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import argparse


class CSVToJSONSerializer:
    """
    A comprehensive tool for converting CSV data to JSON and generating serializer code.
    Supports Django REST Framework, Marshmallow, Pydantic, and custom serializers.
    """

    def __init__(self):
        self.data: List[Dict[str, Any]] = []
        self.field_types: Dict[str, str] = {}
        self.json_data: str = ""

    def load_csv(self, file_path: str, delimiter: str = ',') -> List[Dict[str, Any]]:
        """Load CSV data from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Auto-detect delimiter if not specified
                if delimiter == 'auto':
                    sample = file.read(1024)
                    file.seek(0)
                    sniffer = csv.Sniffer()
                    delimiter = sniffer.sniff(sample).delimiter

                reader = csv.DictReader(file, delimiter=delimiter)

                # Clean headers (remove whitespace)
                fieldnames = [field.strip() for field in reader.fieldnames]

                data = []
                for row in reader:
                    # Clean row data and convert types
                    cleaned_row = {}
                    for key, value in row.items():
                        clean_key = key.strip()
                        clean_value = self._convert_value(value.strip() if value else '')
                        cleaned_row[clean_key] = clean_value
                    data.append(cleaned_row)

                self.data = data
                self._infer_field_types()
                print(f"Successfully loaded {len(self.data)} records from {file_path}")
                return self.data

        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading CSV file: {str(e)}")

    def load_csv_from_string(self, csv_string: str, delimiter: str = ',') -> List[Dict[str, Any]]:
        """Load CSV data from a string."""
        try:
            lines = csv_string.strip().split('\n')
            if not lines:
                raise ValueError("Empty CSV string provided")

            # Auto-detect delimiter if not specified
            if delimiter == 'auto':
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(csv_string[:1024]).delimiter

            reader = csv.DictReader(lines, delimiter=delimiter)

            # Clean headers
            fieldnames = [field.strip() for field in reader.fieldnames]

            data = []
            for row in reader:
                cleaned_row = {}
                for key, value in row.items():
                    clean_key = key.strip()
                    clean_value = self._convert_value(value.strip() if value else '')
                    cleaned_row[clean_key] = clean_value
                data.append(cleaned_row)

            self.data = data
            self._infer_field_types()
            print(f"Successfully loaded {len(self.data)} records from string")
            return self.data

        except Exception as e:
            raise Exception(f"Error parsing CSV string: {str(e)}")

    def _convert_value(self, value: str) -> Union[str, int, float, None]:
        """Convert string values to appropriate Python types."""
        if not value or value.lower() in ['', 'null', 'none', 'n/a']:
            return None

        # Try integer
        if re.match(r'^-?\d+$', value):
            return int(value)

        # Try float
        if re.match(r'^-?\d*\.\d+$', value):
            return float(value)

        # Try boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        return value

    def _infer_field_types(self) -> Dict[str, str]:
        """Infer field types from the data."""
        if not self.data:
            return {}

        field_types = {}
        fields = self.data[0].keys()

        for field in fields:
            values = [row.get(field) for row in self.data if row.get(field) is not None]

            if not values:
                field_types[field] = 'string'
                continue

            # Check for email pattern
            if any('@' in str(v) and '.' in str(v) for v in values):
                field_types[field] = 'email'
            # Check for date pattern
            elif any(self._is_date_string(str(v)) for v in values):
                field_types[field] = 'date'
            # Check for URL pattern
            elif any(str(v).startswith(('http://', 'https://')) for v in values):
                field_types[field] = 'url'
            # Check if all values are integers
            elif all(isinstance(v, int) for v in values):
                field_types[field] = 'integer'
            # Check if all values are floats or integers (numeric)
            elif all(isinstance(v, (int, float)) for v in values):
                field_types[field] = 'float'
            # Check if all values are booleans
            elif all(isinstance(v, bool) for v in values):
                field_types[field] = 'boolean'
            # Default to string
            else:
                field_types[field] = 'string'

        self.field_types = field_types
        return field_types

    def _is_date_string(self, value: str) -> bool:
        """Check if string matches common date patterns."""
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$',  # MM-DD-YYYY
            r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
        ]
        return any(re.match(pattern, value) for pattern in date_patterns)

    def to_json(self, indent: int = 2) -> str:
        """Convert data to JSON string."""
        if not self.data:
            raise ValueError("No data to convert. Load CSV data first.")

        #self.json_data = json.dumps(self.data, indent=indent, default=str)
        self.json_data = json.dumps(self.data)
        print(self.json_data)
        return self.json_data

    def save_json(self, file_path: str, indent: int = 2) -> None:
        """Save JSON data to file."""
        json_str = self.to_json(indent)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(json_str)
        print(f"JSON data saved to {file_path}")

    def generate_django_serializer(self, class_name: str = "Data", validation_level: str = "basic") -> str:
        """Generate Django REST Framework serializer code."""
        if not self.data:
            raise ValueError("No data available. Load CSV data first.")

        field_mapping = {
            'string': 'serializers.CharField',
            'integer': 'serializers.IntegerField',
            'float': 'serializers.FloatField',
            'email': 'serializers.EmailField',
            'date': 'serializers.DateField',
            'url': 'serializers.URLField',
            'boolean': 'serializers.BooleanField',
        }

        code = "from rest_framework import serializers\n\n"
        code += f"class {class_name}Serializer(serializers.Serializer):\n"

        for field, field_type in self.field_types.items():
            django_field = field_mapping.get(field_type, 'serializers.CharField')

            if validation_level == "strict":
                if field_type == 'string':
                    code += f"    {field} = {django_field}(max_length=255, required=True, allow_blank=False)\n"
                elif field_type == 'email':
                    code += f"    {field} = {django_field}(required=True)\n"
                else:
                    code += f"    {field} = {django_field}(required=True)\n"
            elif validation_level == "basic":
                if field_type == 'string':
                    code += f"    {field} = {django_field}(max_length=255)\n"
                else:
                    code += f"    {field} = {django_field}()\n"
            else:  # none
                code += f"    {field} = {django_field}(required=False, allow_null=True)\n"

        if validation_level != "none":
            code += "\n    def validate(self, data):\n"
            code += "        # Add custom validation logic here\n"
            code += "        return data\n"

            code += "\n    def create(self, validated_data):\n"
            code += "        # Implement create logic\n"
            code += "        return validated_data\n"

            code += "\n    def update(self, instance, validated_data):\n"
            code += "        # Implement update logic\n"
            code += "        for attr, value in validated_data.items():\n"
            code += "            setattr(instance, attr, value)\n"
            code += "        return instance\n"

        return code

    def generate_marshmallow_serializer(self, class_name: str = "Data", validation_level: str = "basic") -> str:
        """Generate Marshmallow schema code."""
        if not self.data:
            raise ValueError("No data available. Load CSV data first.")

        field_mapping = {
            'string': 'fields.Str',
            'integer': 'fields.Int',
            'float': 'fields.Float',
            'email': 'fields.Email',
            'date': 'fields.Date',
            'url': 'fields.Url',
            'boolean': 'fields.Bool',
        }

        code = "from marshmallow import Schema, fields, validate, post_load\n\n"
        code += f"class {class_name}Schema(Schema):\n"

        for field, field_type in self.field_types.items():
            marshmallow_field = field_mapping.get(field_type, 'fields.Str')

            if validation_level == "strict":
                if field_type == 'string':
                    code += f"    {field} = {marshmallow_field}(required=True, validate=validate.Length(min=1, max=255))\n"
                elif field_type == 'email':
                    code += f"    {field} = {marshmallow_field}(required=True)\n"
                else:
                    code += f"    {field} = {marshmallow_field}(required=True)\n"
            elif validation_level == "basic":
                code += f"    {field} = {marshmallow_field}()\n"
            else:  # none
                code += f"    {field} = {marshmallow_field}(allow_none=True, missing=None)\n"

        code += f"\n    @post_load\n"
        code += f"    def make_{class_name.lower()}(self, data, **kwargs):\n"
        code += f"        return {class_name}(**data)\n"

        # Add the data class
        code += f"\n\nclass {class_name}:\n"
        code += f"    def __init__(self, **kwargs):\n"
        for field in self.field_types.keys():
            code += f"        self.{field} = kwargs.get('{field}')\n"

        return code

    def generate_pydantic_model(self, class_name: str = "Data", validation_level: str = "basic") -> str:
        """Generate Pydantic model code."""
        if not self.data:
            raise ValueError("No data available. Load CSV data first.")

        field_mapping = {
            'string': 'str',
            'integer': 'int',
            'float': 'float',
            'email': 'EmailStr',
            'date': 'date',
            'url': 'AnyHttpUrl',
            'boolean': 'bool',
        }

        imports = ["from pydantic import BaseModel, validator"]
        if 'email' in self.field_types.values():
            imports.append("from pydantic import EmailStr")
        if 'url' in self.field_types.values():
            imports.append("from pydantic import AnyHttpUrl")
        if 'date' in self.field_types.values():
            imports.append("from datetime import date")

        code = ", ".join(imports) + "\n"
        code += "from typing import Optional\n\n"
        code += f"class {class_name}(BaseModel):\n"

        for field, field_type in self.field_types.items():
            pydantic_type = field_mapping.get(field_type, 'str')

            if validation_level == "strict":
                code += f"    {field}: {pydantic_type}\n"
            elif validation_level == "basic":
                code += f"    {field}: Optional[{pydantic_type}] = None\n"
            else:  # none
                code += f"    {field}: Optional[{pydantic_type}] = None\n"

        if validation_level != "none":
            code += "\n    class Config:\n"
            code += "        # Pydantic configuration\n"
            code += "        validate_assignment = True\n"
            code += "        use_enum_values = True\n"

            # Add custom validators for strict validation
            if validation_level == "strict":
                for field, field_type in self.field_types.items():
                    if field_type == 'string':
                        code += f"\n    @validator('{field}')\n"
                        code += f"    def validate_{field}(cls, v):\n"
                        code += f"        if not v or len(v.strip()) == 0:\n"
                        code += f"            raise ValueError('{field} cannot be empty')\n"
                        code += f"        return v.strip()\n"

        return code

    def generate_dataclass(self, class_name: str = "Data", validation_level: str = "basic") -> str:
        """Generate Python dataclass code."""
        if not self.data:
            raise ValueError("No data available. Load CSV data first.")

        field_mapping = {
            'string': 'str',
            'integer': 'int',
            'float': 'float',
            'email': 'str',
            'date': 'str',
            'url': 'str',
            'boolean': 'bool',
        }

        code = "from dataclasses import dataclass, field\n"
        code += "from typing import Optional, List, Dict, Any\n"
        if 'date' in self.field_types.values():
            code += "from datetime import datetime\n"
        code += "\n"

        code += "@dataclass\n"
        code += f"class {class_name}:\n"

        for field_name, field_type in self.field_types.items():
            python_type = field_mapping.get(field_type, 'str')

            if validation_level == "strict":
                code += f"    {field_name}: {python_type}\n"
            else:
                code += f"    {field_name}: Optional[{python_type}] = None\n"

        # Add utility methods
        code += "\n    @classmethod\n"
        code += f"    def from_dict(cls, data: Dict[str, Any]) -> '{class_name}':\n"
        code += "        return cls(**data)\n"

        code += "\n    def to_dict(self) -> Dict[str, Any]:\n"
        code += "        return {\n"
        for field_name in self.field_types.keys():
            code += f"            '{field_name}': self.{field_name},\n"
        code += "        }\n"

        code += "\n    @classmethod\n"
        code += f"    def from_json_file(cls, file_path: str) -> List['{class_name}']:\n"
        code += "        import json\n"
        code += "        with open(file_path, 'r') as f:\n"
        code += "            data = json.load(f)\n"
        code += "        return [cls.from_dict(item) for item in data]\n"

        return code

    def print_summary(self) -> None:
        """Print a summary of the loaded data."""
        if not self.data:
            print("No data loaded.")
            return

        print(f"\n{'=' * 50}")
        print("DATA SUMMARY")
        print(f"{'=' * 50}")
        print(f"Records loaded: {len(self.data)}")
        print(f"Fields: {len(self.field_types)}")
        print(f"\nField Types:")
        for field, field_type in self.field_types.items():
            print(f"  {field:20} -> {field_type}")

        print(f"\nSample Record:")
        if self.data:
            for key, value in list(self.data[0].items())[:5]:  # Show first 5 fields
                print(f"  {key:20} -> {value}")

    def save_serializer(self, serializer_type: str, file_path: str, class_name: str = "Data",
                        validation_level: str = "basic") -> None:
        """Save serializer code to file."""
        serializer_generators = {
            'django': self.generate_django_serializer,
            'marshmallow': self.generate_marshmallow_serializer,
            'pydantic': self.generate_pydantic_model,
            'dataclass': self.generate_dataclass,
        }

        if serializer_type not in serializer_generators:
            raise ValueError(f"Unknown serializer type: {serializer_type}")

        code = serializer_generators[serializer_type](class_name, validation_level)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(code)

        print(f"{serializer_type.capitalize()} serializer saved to {file_path}")


def create_sample_csv(file_path: str = "sample_data.csv") -> None:
    """Create a sample CSV file for testing."""
    sample_data = """name,age,email,department,salary,is_active,start_date,website
John Doe,30,john@example.com,Engineering,75000.50,true,2023-01-15,https://johndoe.dev
Jane Smith,25,jane@example.com,Marketing,65000.00,true,2023-03-20,https://janesmith.com
Bob Johnson,35,bob@example.com,Sales,80000.25,false,2022-11-10,
Alice Brown,28,alice@example.com,Design,70000.00,true,2023-05-01,https://alicebrown.design
Charlie Wilson,32,charlie@example.com,Engineering,85000.75,true,2022-08-15,https://charlie.dev"""

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(sample_data)

    print(f"Sample CSV created: {file_path}")


def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description="CSV to JSON to Serializer Converter")
    parser.add_argument("--csv", help="Path to CSV file")
    parser.add_argument("--output", help="Output directory", default="output")
    parser.add_argument("--class-name", help="Class name for serializer", default="Data")
    parser.add_argument("--validation", choices=["none", "basic", "strict"], default="basic")
    parser.add_argument("--create-sample", action="store_true", help="Create sample CSV file")

    args = parser.parse_args()

    # Create output directory
    Path(args.output).mkdir(exist_ok=True)

    # Create sample if requested
    if args.create_sample:
        create_sample_csv("sample_data.csv")
        return

    # Initialize converter
    converter = CSVToJSONSerializer()

    # Use sample data if no CSV provided
    if not args.csv:
        print("No CSV file provided. Using sample data...")
        create_sample_csv("sample_data.csv")
        args.csv = "sample_data.csv"

    try:
        # Load CSV
        converter.load_csv(args.csv)
        converter.print_summary()

        # Save JSON
        json_file = Path(args.output) / f"{args.class_name.lower()}.json"
        converter.save_json(str(json_file))

        # Generate and save serializers
        serializers = ['django', 'marshmallow', 'pydantic', 'dataclass']

        for serializer_type in serializers:
            file_name = f"{args.class_name.lower()}_{serializer_type}_serializer.py"
            file_path = Path(args.output) / file_name

            try:
                converter.save_serializer(
                    serializer_type,
                    str(file_path),
                    args.class_name,
                    args.validation
                )
            except Exception as e:
                print(f"Error generating {serializer_type} serializer: {e}")

        print(f"\nAll files saved to: {args.output}")
        print("\nGenerated files:")
        for file_path in Path(args.output).glob("*"):
            print(f"  - {file_path.name}")

    except Exception as e:
        print(f"Error: {e}")


# Example usage
if __name__ == "__main__":
    # Run CLI if called directly
    import sys

    HOST = '127.0.0.1'  # Connect to local server
    PORT = 5000

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #client.connect((HOST, PORT))

    if len(sys.argv) > 1:
        main()
    else:
        # Interactive example
        print("CSV to JSON to Serializer Converter")
        print("=" * 40)

        # Create and use sample data
        create_sample_csv()

        converter = CSVToJSONSerializer()
        converter.load_csv("sample_data.csv")
        converter.print_summary()

        # Convert to JSON
        json_data = converter.to_json()
        converter.save_json("json_data")

        json_data_as_bytes = str.encode(json_data)

        client.sendall(json_data_as_bytes)
        data = client.recv(1024)
        print(f"Received: {data.decode()}")

        client.close()
