# TODO: Consider print chore query in case echoes are missed
# TODO: Consider print chore query for parallelization
# TODO: Consider merging into crosscompute workers run


async def make_archive(is_ready, print_folder, file_url):
    while not is_ready():
        await asyncio.sleep(1)
    archive_path = archive_safely(print_folder)
    with open(archive_path, 'rb') as data:
        response = requests.put(file_url, data=data)
        print(response.__dict__)
    rmtree(print_folder)
    remove(archive_path)
