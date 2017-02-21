
# ### Number of topics (not unique)
def numTopics(unique=False):
    if unique:
        count = 0
        for key in dictionary.keys():

            for innerkey in dictionary[key].keys():
                count += len(dictionary[key][innerkey])
        return count
    else:
        
        return 



# In[39]:

