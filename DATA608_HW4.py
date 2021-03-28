# -*- coding: utf-8 -*-
"""
Mario Pena
DATA608_HW4
3/28/2021
"""

#Packages loaded for assignment.
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd


#Define a function that uses SoQL functions within to pull(query) desired data 
#and avoid the limits of the API.
#The parameters are ultimately the SoQL functions used to query the data.
#The 'for' loop is used to build the url containing SoQL functions to pull data from a .json file.
def get_url(**kwargs):
    url = 'https://data.cityofnewyork.us/resource/nwxe-4ae8.json?'
    params = []
    for k, v in kwargs.items():
        if type(v) == list:
            v = '&'.join(v)
        params.append('$' + k + '=' + v)
    return (url + '&'.join(params)).replace(' ', '%20')

#Initialize Dash by calling the Dash class of dash.
app = dash.Dash()

#This is added when deploying the app.
#server = app.server

#Created a list of New York City boros.
boro_list = ['Bronx', 'Brooklyn', 'Manhattan', 'Queens', 'Staten Island']

#Created a list of the common tree species with previously defined 'get_url' function.
#Used pandas read_json function to read the .json file from the web.
#Had to create a 2nd list and slice it to 132 as the first list created consisted
# of 133 rows and the Dash app was giving an error when trying to display
#the drop down menu (Correct number of options is 132).
species_url = get_url(select='spc_common', group='spc_common', order='spc_common')
species = pd.read_json(species_url)
species_list = list(species['spc_common'])
species_list2 = species_list[:132]

#Create the layout of the application.
app.layout = html.Div([
        #Title.
        html.Div([
            html.H3('New York City Tree Health by Species & Stewardship')
        ], style={'textAlign' : 'center'}),
   
        #First dropdown title and menu.
        #Options taken from the 'boro_list' previously created.
        html.Div([
            html.Label('Select a NYC Boro'),
            dcc.Dropdown(
                id='boro_choice',
                options=[{'label': i, 'value': i} for i in boro_list],
                value='Bronx')
        ], style={'padding' : 1, 'width': '20%', 'float': 'center'}),
        
        #Second dropdown title and menu.
        #Options taken from the 'species_list2' previously created.
        html.Div([
            html.Label('Select a Tree Species'),
            dcc.Dropdown(
                id='species_choice',
                options=[{'label': i, 'value': i} for i in species_list2],
                value='American beech')
        ], style={'padding' : 1, 'width': '20%', 'float': 'center'}),
        
        #First graph display (proportions)
        html.Div([
            dcc.Graph(id='prop_graph')
        ], style={'width': '48%', 'float': 'left', 'display': 'inline-block'}),
        
        #Second graph dispslay (numbers)
        html.Div([
            dcc.Graph(id='num_graph')
        ], style={'width': '48%', 'float': 'left', 'display': 'inline-block'})

    ], style={'padding': 20, 'font-family': 'Garamond'})

#Bind callback function to HTML input field to make our app interactive with user input.
#Create graph to show proportions.
@app.callback(
    Output('prop_graph', 'figure'), #Output is graph.
    [Input('boro_choice', 'value'), #User input is choice of 'boro' and tree 'species'.
     Input('species_choice', 'value')])

#Define function that updates proportions graph based on user input.
def update_output(boro_choice, species_choice):

    #Pulled data from web using previously defined 'get_url' function.
    #Selected columns desired for analysis and bound to be limited by
    #selection of 'species' and 'boro' (user input). (This avoids limit of API).
    url = get_url(select='health,steward,count(tree_id)',
                  where=[
                      "spc_common='" + species_choice + "'",
                      "boroname='" + boro_choice + "'"
                  ],
                  group='spc_common,health,steward',
                  order='spc_common,steward,health')
    
    #Used pandas read_json function to read the .json file from the web.
    trees = pd.read_json(url)

    #Change the value of 'None' in column 'steward' to '0-None'.
    trees.loc[trees['steward'] == 'None', 'steward'] = '0-None'

    #Convert 'steward' and 'health' fields to categories.
    #Sort and and re-order data based on categories and unique values of categories.
    trees[['steward', 'health']] = trees[['steward', 'health']].astype('category')
    steward_cat = list(trees['steward'].unique())
    steward_cat.sort()
    trees['steward'] = trees['steward'].cat.reorder_categories(steward_cat)
    h_cat = ['Good', 'Fair', 'Poor']
    health_cat = sorted(list(trees['health'].unique()), key=lambda x: h_cat.index(x))
    trees['health'] = trees['health'].cat.reorder_categories(health_cat)
    
    #Calculate proportion
    prop = trees.groupby(['steward', 'health']).agg({'count_tree_id': 'sum'}).groupby(level=0).apply(
        lambda g: g / g.sum()).reset_index()

    #Create bar chart with hover text
    traces = []
    colors = ['#9972af', '#c8ada0', '#c8b35a']
    i = 0
    for h in prop.health.cat.categories.tolist():
        prop_health = prop[prop['health'] == h]
        traces.append(go.Bar(
            x=prop_health['steward'],
            y=prop_health['count_tree_id'],
            marker=dict(color=colors[i]),
            name=h
        ))
        i += 1

    #Return the graph created for update_output function.
    return {
        'data': traces,
        'layout': go.Layout(
            title='Health of Trees in Proportion by Stewardship:',
            barmode='group',
            xaxis={
                'title': 'Stewardship'
            },
            yaxis={
                'title': 'Proportion of Trees in Good, Fair or Poor Health'
            }
        )
    }


#Bind callback function to HTML input field to make our app interactive with user input.
#Create graph to show numbers.
@app.callback(
    Output('num_graph', 'figure'), #Output is the graph.
    [Input('boro_choice', 'value'), #User input is choice of 'boro' and tree 'species'.
     Input('species_choice', 'value')])

#Define function that updates proportions graph based on user input.
def update_output2(boro_choice, species_choice):
    
    #Pulled data from web using previously defined 'get_url' function.
    #Selected columns desired for analysis and bound to be limited by
    #selection of 'species' and 'boro' (user input). (This avoids limit of API).
    url = get_url(select='health,steward,count(tree_id)',
                  where=[
                      "spc_common='" + species_choice + "'",
                      "boroname='" + boro_choice + "'"
                  ],
                  group='spc_common,health,steward',
                  order='spc_common,steward,health')
    
    #Used pandas read_json function to read the .json file from the web.
    trees = pd.read_json(url)

    #Change the value of 'None' in column 'steward' to '0-None'.
    trees.loc[trees['steward'] == 'None', 'steward'] = '0-None'
    
    #Convert 'steward' and 'health' fields to categories.
    #Sort and and re-order data based on categories and unique values of categories.
    trees[['steward', 'health']] = trees[['steward', 'health']].astype('category')
    steward_cat = list(trees['steward'].unique())
    steward_cat.sort()
    trees['steward'] = trees['steward'].cat.reorder_categories(steward_cat)
    h_cat = ['Good', 'Fair', 'Poor']
    health_cat = sorted(list(trees['health'].unique()), key=lambda x: h_cat.index(x))
    trees['health'] = trees['health'].cat.reorder_categories(health_cat)
    
    #Create bar chart with hover text.
    traces = []
    colors = ['#9972af ', '#c8ada0', '#c8b35a']
    i = 0
    for h in trees.health.cat.categories.tolist():
        trees_health = trees[trees['health'] == h]
        traces.append(go.Bar(
            x=trees_health['steward'],
            y=trees_health['count_tree_id'],
            marker=dict(color=colors[i]),
            name=h
        ))
        i += 1

    #Return the graph created for update_output2 function.
    return {
        'data': traces,
        'layout': go.Layout(
            title='Health of Trees in Numbers by Stewardship',
            barmode='group',
            xaxis={
                'title': 'Stewardship'
            },
            yaxis={
                'title': 'Number of Trees in Good, Fair or Poor Health'
            }
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True)
