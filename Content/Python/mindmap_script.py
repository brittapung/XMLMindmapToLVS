from collections import defaultdict
import logging
import os
import re
import sys
import unreal
import xml.etree.ElementTree as ET

default_lvs_directory = '/Game'
default_namespace = 'http://schemas.microsoft.com/project'


class TreeNode:
	"""
	TreeNode class

	Parameters:
		name - name as a string
		outline_number - mindmap node number
		outline_level - mindmap node level
		children - list of children TreeNodes
	"""
	def __init__(self, name, outline_number, outline_level):
		self.name = name
		self.outline_number = outline_number
		self.outline_level = outline_level
		self.children = []

	def add_child(self, child):
		self.children.append(child)

	def __str__(self):
		return str(self.outline_number) + ' ' + str(self.outline_level) + ' ' + self.name + ' '\
			+ str(len(self.children)) + ' children'


def process_xml(file_path):
	"""
	Process mindmap data in given XML file and create respective Level Variant Sets in Unreal project

	:param file_path: Mindmap XML file path
	"""
	logging.info("Script execution starting")
	xml_data = read_xml_file(file_path)
	root_node = process_tasks(xml_data)
	create_level_variant_sets(root_node)
	logging.info("Script execution finished")


def read_xml_file(file_path):
	"""
	Reads given XML file and returns the file as a string

	:param file_path: XML file path
	:return: XML file contents as a string
	"""
	logging.info("Reading file:")
	logging.info(file_path)

	# Remove invisible character that might show up if copying path from Windows properties window
	file_path = file_path.strip("‪")

	if not os.path.isfile(file_path):
		quit_execution("File doesn't exist")
	elif not file_path.endswith(".xml"):
		quit_execution("Must be an XML file")
	return ET.parse(file_path).getroot()


def process_tasks(xml_data):
	"""
	Parses given XML mindmap data in to a hierarchical format

	:param xml_data: XML data as a string
	:return: TreeNode of top level (company) mindmap node
	"""
	logging.info("Parsing XML data")

	ns = namespace(xml_data)
	namespaces = {'ns': ns}

	tasks = xml_data.find('ns:Tasks', namespaces)
	tasks_list = []
	for task in tasks:
		name = task.find('ns:Name', namespaces).text
		outline_number = str(task.find('ns:OutlineNumber', namespaces).text)
		outline_level = int(task.find('ns:OutlineLevel', namespaces).text)
		tasks_list.append({'name': name, 'outline_number': outline_number, 'outline_level': outline_level})

	return recursive_loop(tasks_list)


def recursive_loop(rest_of_tasks_list):
	"""
	Loops through mindmap data recursively to create hierarchical TreeNode model

	:param rest_of_tasks_list: Unprocessed part of tasks list
	:return: Current top-level TreeNode that includes a list of any children
	"""
	current_task = rest_of_tasks_list.pop(0)
	current_node = TreeNode(current_task['name'], current_task['outline_number'], current_task['outline_level'])

	if len(rest_of_tasks_list) == 0:
		return current_node

	# Add children
	current_outline_number = current_task['outline_number']
	next_outline_number = rest_of_tasks_list[0]['outline_number']
	while len(next_outline_number) > len(current_outline_number):
		current_node.add_child(recursive_loop(rest_of_tasks_list))
		if len(rest_of_tasks_list) == 0:
			break
		next_outline_number = rest_of_tasks_list[0]['outline_number']

	return current_node


def create_level_variant_sets(root_node):
	"""
	Create UE5 Level Variant Set objects for given TreeNode product tree

	Outline levels:
	1 - company name
	2 - products
	3 - variant sets
	4 - variants

	:param root_node: Root of the TreeNode product tree
	"""
	logging.info("Creating Level Variant Sets")

	if root_node.name:
		lvs_directory = default_lvs_directory + '/' + root_node.name.replace(' ', '_') + '_LVS'
	else:
		lvs_directory = default_lvs_directory

	for product_node in root_node.children:
		lvs_path = lvs_directory + '/' + product_node.name.replace(' ', '_')
		if unreal.EditorAssetLibrary.does_asset_exist(lvs_path):
			lvs = unreal.EditorAssetLibrary.load_asset(lvs_path)
		else:
			lvs = unreal.VariantManagerLibrary.create_level_variant_sets_asset(product_node.name, lvs_directory)

		variant_set_dict = get_variants_dict(product_node)
		for variant_set, variants in variant_set_dict.items():
			split_vs = variant_set.split('.')
			vs_name = '.'.join(split_vs[1:]).replace(' ', '_')

			vs = lvs.get_variant_set_by_name(vs_name)
			if vs is None:
				vs = unreal.VariantSet()
				vs.set_display_text(vs_name)
				unreal.VariantManagerLibrary.add_variant_set(lvs, vs)
			for variant_name in variants:
				variant = vs.get_variant_by_name(variant_name.replace(' ', '_'))
				if variant is None:
					variant = unreal.Variant()
					variant.set_display_text(variant_name.replace(' ', '_'))
					unreal.VariantManagerLibrary.add_variant(vs, variant)


def get_variants_dict(product_node):
	"""
	Gets recursive list of variants for the given node and collates into a dictionary

	:param product_node: The product node to get variants for
	:return: A dictionary where the keys are variant sets and the values are lists of variants
	"""
	variants_list = get_variants_list(product_node, '')

	variant_set_dict = defaultdict(list)
	for variant_dict in variants_list:
		for key, value in variant_dict.items():
			variant_set_dict[key].append(value)

	return variant_set_dict


def get_variants_list(variant_set_node, prefix):
	"""
	Loops through product nodes recursively and returns all variants for a product

	:param variant_set_node: Current product or property node
	:param prefix: Current prefix to add to the variant set name
	:return: A list of dictionaries where the keys are variant sets and the values are variants
	"""
	variants_list = []

	for child in variant_set_node.children:
		if not child.children:
			variant_set = '.'.join([prefix, variant_set_node.name])
			variants_list.append({variant_set: child.name})
		else:
			variants_list += get_variants_list(child, '.'.join([prefix, variant_set_node.name]).strip('.'))

	return variants_list


def quit_execution(error_message):
	"""Log error message and quit program execution"""
	logging.error(error_message)
	sys.exit()


def namespace(element):
	"""Parse 'xmlns' tag from XML data"""
	m = re.match(r'\{.*}', element.tag)
	return m.group(0)[1:-1] if m else default_namespace


if __name__ == '__main__':
	logging.info(str(sys.argv))
	process_xml('C:\\Users\\Admin\\Desktop\\[AVAR TEMPLATE] Company name - Copy.xml')
