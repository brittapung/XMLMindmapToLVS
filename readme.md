XMLMindmapToLVS
===============
Author: Britta Pung
Date: 22.11.2022

Description:
------------
XMLMindmapToLVS is an Unreal plugin which reads XML data from mindomo.com and creates relevant UE5 Level Variant Sets.

Input:
------
XML file from mindomo.com. The mindmap should have a max depth of 4. The root of the tree should be a node that contains the name of the company.
Second level nodes contain the names of products (Level Variant Sets), third level nodes contain names of product features (Variant Sets) and
fourth level nodes contain the different Variants of a given feature.

Output:
-------
Level Variant Set objects for every product which contain the relevant variant sets and variants.

Installation:
-------------
1. Go to your Unreal project's folder and create a folder called 'Plugins' if you don't have one yet.
2. Place the 'XMLMindmapToLVS' folder in the Plugins folder.
3. Restart Unreal Engine if you had it open.

Using the plugin:
-----------------
1. Run the XMLMindmapToLVS Editor Utility Widget.
2. Input the direct path of your XML file.
3. Press the run button.

Required plugins:
-----------------
1. Editor Scripting Utilities
2. Python Editor Script
3. Variant Manager
