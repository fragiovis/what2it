USAGE LICENSE
Creative Commons Attribution 4.0 International Public License

FILE CONTENTS
dataset
|_ foods					folder containing files of food dataset (starting data from giallozafferano.it)
|  |_ CSV					folder containing files in .csv format
|  |  |_ categories.csv			
|  |  |_ foodDataset.xlsx			each of other .csv files derived from sheet of this excel file
|  |  |_ ingredients.csv			
|  |  |_ ingredientsClasses.csv		
|  |  |_ ingredientsMetaclasses.csv	
|  |  |_ preparations.csv			
|  |  |_ recipes.csv			
|  |_ TXT					folder containing files in .txt format
|     |_ scorpored values			folder containing values in textData scorpored by type of data
|     |  |_ category-cost-difficulty.txt
|     |  |_ ingredients.txt
|     |  |_ names.txt
|     |  |_ preparations.txt
|     |  |_ preparationTime.txt
|     |_ textData.txt				.txt version of dataset/foods/CSV/foodDataset.xlsx file
|_ survey_answers				folder containing results of the surveys on food preferences of the dataset
|  ├─ sorts					folder containing results of the three surveys' questions where users sort foods
|  |  ├─ ID					folder containing the sorts identifying foods by their ID
|  |  |  |_ sort1.csv				the three csv files contain the survey id, and then the food ordered by the user
|  |  |  |_ sort2.csv
|  |  |  |_ sort3.csv
|  |  |_ Name					folder containing the sorts identifying foods by their names (in italian)
|  |     |_ sort1.csv				the three csv files contain the survey id, and then the food ordered by the user
|  |     |_ sort2.csv
|  |     |_ sort3.csv
|  ├─ answers.csv				results of the surveys
|  |_ labels.txt				labels of the samples in samples.txt 
|  |_ samples.txt				couples of food in pairwise comparison form [1] extracted from the sorts
|_ survey_of_return				folder containing the results of survey of returns
|  |_ theories					folder containing the theories used to build the survey of returns
|  |  |_ 10
|  |  |_ ...					folders relative to the i-th user theories
|  |  |_ 43
|  |     |_ global-indirectPCA-8PC2STD.las	.las file from which the relative theory is returned using ILASP
|  |     |_ global-indirectPCA-8PC2STD.txt	.txt file containing the returned theory by ILASP of relative case
|  |     |_ global-indirectPCA-17PC2STD.las
|  |     |_ global-indirectPCA-17PC2STD.txt
|  |     |_ global-noPCA.las
|  |     |_ global-noPCA.las
|  |     |_ local-indirectPCA-8PC2STD.las
|  |     |_ local-indirectPCA-8PC2STD.las
|  |_ 10.csv					.csv files containing the survey of return results relative to the i-t user
|  |_ ...
|  |_ 43.csv
|_ readme.md
|_ readme.txt				

RECIPES DATASET DESCRIPTION
the description refer to dataset/foods/CSV/foodDataset.xlsx
Name			italian name of the recipe
ID			ID associated to the recipe
Link			link of where the food data has been get
Category Name		name of the category (Starter, Complete Meal, First Course, Second Course, Savoury Cake)
Category ID		ID associated to the category
Cost			cost indicator of the food, discrete interval from 1 to 5
Difficulty		difficuly indicator of the food, discrete interval from 1 to 4
Preparation Time	integer positive number that indicates preparation time of the food expressed in minutes
Ingredient		english name of an ingredient of the recipe
Ingredient ID		ID associated to the ingredient.
W			weight that the ingredient has in the composition of the interested recipe
NOTE: the last three columns repeats for 18 times, leaving empty spaces when the recipe has no ingredients other than those already entered
Preparation		english name of a preparation performed on the recipe
Preparation ID		ID associated to the preparation
W			weight that the preparation has in the composition of the interested recipe
NOTE: the last three columns repeats for 5 times similarly to ingredients

in other sheet of the file are reportet all the ingredients, divided in classes and metaclasses, preparations and categories

NOTE: in dataset/foods/TXT/textData.txt ingredients and preparation has been vectorized as follow:
- each element of the ingredient vector represent the weight of the ingredient class in the recipe. The weight of an ingredient class in a recipe is collected by sum up the weight of the ingredients owned by that particular ingredient class in the recipe.
- each element of the preparation vector represent the weight of the preparation in the recipe.

PREFERENCES DATASET DESCRIPTION
In the file *dataset/survey_answers/answer.csv* are reported the 54 user's answers to the surveys, formatted in the following format:
UserID						ID associated to the user                                                                                                                         
Survey ID					ID of the survey which user has answered                                                                                                           
Answer ID					ID of the answer respect to the survey                                                                                                            
Gender                                  	Gender of the user                                                                                                                                
AgeRange                                	Age Range of the user                                                                                                                             
Region                                  	Italian Region of the user                                                                                                                        
Food1                                   	Rating of the first recipe proposed to the user                                                                                                   
...                                     	the following are rating of the other food proposed to the user                                                                                   
Food21                                  	rating of the twenty-first food proposed to the user                                                                                              
Sort-Name1                              	first sort of three requested to the user during the survey, in which food are identified by name                                                 
Sort-Name2                              	second sort of three requested to the user during the survey, in which food are identified by name                                                
Sort-Name3                              	third sort of three requested to the user during the survey, in which food are identified by name                                                 
Sort-ID1                                	first sort of three requested to the user during the survey, in which food are identified by ID                                                   
Sort-ID2                                	second sort of three requested to the user during the survey, in which food are identified by ID                                                  
Sort-ID3                                	third sort of three requested to the user during the survey, in which food are identified by ID                                                   
Class-Citrus                            	Rating of the user about the ingredient class "Citrus"                                                                                            
...                                     	the following are rating of the other ingredient classes                                                                                          
Class-Yogurt                            	Rating of the user about the ingredient class "Yogurt"                                                                                            
Metaclass-Meat                          	Rating of the user about the ingredient metaclass "Meat"                                                                                          
...                                     	the following are rating of the other ingredient metaclasses                                                                                      
Metaclass-Vegetables                    	Rating of the user about the ingredient metaclass "Vegetables"                                                                                    
Preparation-Boiling                     	Ratibg of the user about the preparation "Boiling"                                                                                                
...                                     	the following are rating of the other preparations                                                                                                
Preparation-Stewing                     	Rating of the user about the preparation "Stewing"                                                                                                
Difficulty                              	rating of the user respect to recipes which preparation difficulties are generally higher                                                         
PreparationTime                         	rating of the user respect to recipes which preparation time is generally higher                                                                  
Cost                                    	rating of the user respect to recipes which cost is generally higher                                                                              
ParticularCase1-Ingredient/Preparation1 	first ingredient/preparation of a particular combination of ingredients/preparations for which previous expressed preferences are no longer valid [2]
ParticularCase2-Ingredient/Preparation1 	second ingredient/preparation of particular combination of ingredients/preparations for which previous expressed preferences are no longer valid [2]                             
ParticularCase3-Ingredient/Preparation1 	third ingredient/preparation of particular combination of ingredients/preparations for which previous expressed preferences are no longer valid [2]         
ParticularCase1-rating                  	rating of the particular combination of ingredients/preparations expressed with previously three columns                                          
...                                     	following are other particular combination of ingredients/preparation                                                                             

Note that the Sort-Name and Sort-ID columns are also reported in form of *.csv* files, respectevely in the folders *dataset/survey_answers/sorts/Name* and *dataset/survey_answers/sorts/ID*.

In the file *dataset/survey_answer/samples.txt* are reported 54 user's orderings in the form of *pairwise comparison*. Thus for each row correspond the ordering of a user. The ordering is written in the form of pairwise comparison, so each element of the ordering are paired with all others (avoiding simmetries). 
For instance, given the recipes as their ID:

1;2;3

becomes:

1,2;1,3;2,3

The file is written following the *.csv* format.
In the file *dataset/survey_answer/lables.txt* are written the corresponding labels of the couples.
The label has value 1 if the first element of the couple is preferred over the second, -1 if the second element is preferred over the first, 0 if there is uncertainity about which of the element is preferred.

SURVEY OF RETURN
In the folder survey of return are reported the .csv files containing the result of survey of return of each user and the theories used to create the respective surveys.
The used theories are those obtained after training ILASP both as global and local approximator.
In global approximator we considered both the cases in which PCA is involved and not involved (considering only the indirect case with PC=8, 17 when involved).
In local approximator we considered only the case in which PCA is involved indirectly with PC = 8 (considering std for gaussian noise equal to 0.1).
More detail are reported in the "HOW TO CITE" correlated paper.
In the folder are also returned the .las files containing the file used to train ILASP (version 4.2.0).

NOTES:
[1] 
Each sample has the form <IDfood1, IDfood2> and has label 1 if IDfood1 is preferred over IDfood2, -1 if IDfood2 is preferred over IDfood1, 0 if there is indifference relationship over IDfood1 and IDfood2.

The preference sorts have been translated into pairwise comparison in two phases:
 1- search of inconsistencies among the three sorts in order to get the "certain" preference relationships
 2- search of transitivity of preferences among the "certain" couples, giving indifference relationship to those for which no transitivity has been found.

More details about these two phases and a pseudo-code can be found in the article attached with this dataset

[2]

During the survey we proposed to the user to indicate metaclasses if the particular combination applies for all classes owned by that specific metaclass, or to indicate classes if the particular combination apply only for that specific class. 
To Identify classes from metaclasses, since their name could be misleading, we denoted classes with the prefix "---". 
We left this notation also in the final dataset, since could be useful to easily recognize classes from metaclasses withouth looking to the files regarding them.


HOW TO CITE:
D.Fossemò, F.Mignosi, L.Raggioli, M.Spezialetti, F.A.D'Asaro. Using Inductive Logic Programming to globally approximate Neural Networks for preference learning: challenges and preliminary results. BEWARE-22, co-located with AIxIA 2022, November 28-December 2, 2022, University of Udine, Udine, Italy.



