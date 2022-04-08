# code_insights

Read your code into a mongodb database for analysis.

Example:

Get the average number of files per commit per user:

```python
[
    {
        '$addFields': {
            'file_count': {
                '$size': '$files'
            }
        }
    }, {
        '$group': {
            '_id': '$author', 
            'avg_files': {
                '$avg': '$file_count'
            }
        }
    }, {
        '$sort': {
            'avg_files': -1
        }
    }
]
```


## Testing

Testing is done via pytest.

```
$ poetry run pytest
```
