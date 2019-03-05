import os
import re
import urllib.parse

from dateutil import parser
from datetime import datetime
from jinja2 import Template


class Index():

    def __init__(self):
        template_file = open('./templates/index.html', 'r')
        template_file_content = template_file.read()
        template_file.close()

        self.template = Template(template_file_content)

    def generate_index(self):
        item_objects = []
        for folder in os.walk('.'):
            feed_title = folder[0]

            if feed_title == '.' or feed_title == '' or feed_title == './templates':
                continue

            items = folder[2]

            for item in items:
                item_object = {}
                time_match = re.match(r'(.+\d{2}:?\d{2})_-_', item)

                if time_match:
                    # Time string at the beginning
                    time_string = time_match.group(0)
                    item_object['time'] = time_match.group(1)
                    item_name = item.replace(time_string, '')
                else:
                    # No time string at the beginning
                    item_object['time'] = str(datetime.now())
                    item_name = item

                location = feed_title + '/' + item
                location = urllib.parse.quote(location[2:])
                item_object['location'] = location
                item_object['name'] = item_name[:-5]
                item_objects.append(item_object)

        item_objects = sorted(
            item_objects,
            key=lambda item: parser.parse(item['time']),
            reverse=True)

        return self.template.render(item_objects=item_objects)
