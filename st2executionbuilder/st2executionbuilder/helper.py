def get_parent_array(changelog):
    def parents(parent, parents_list):
        parents_list.append(parent['execution_id'])
        if 'parent' in parent:
            parents(parent['parent'], parents_list)

    parents_array = [changelog['execution_id']]

    if 'context' in changelog and 'parent' in changelog['context']:
        parents(changelog['context']['parent'], parents_array)

    return parents_array



def update_parent_execution_graph(children, parents_array, index, changelog, last_node):
    if children['id'] == parents_array[index]:
        if index == 0:
            children['status'] = changelog['status']
            children['name'] = changelog['name']
            return True

        for child in children['children']:
            if update_parent_execution_graph(child, parents_array, index - 1, changelog, last_node):
                return True

        children['children'].append(
            {'children': [], 'status': changelog['status'], 'name': changelog['name'], 'id': changelog['execution_id']})
        return True
