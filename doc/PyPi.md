# PyPi Cheatsheet

How to upload a new package release into PyPi

## Prerequisites

	- Needs an account in PyPi and Testing PyPy

	- Have your  ~/.pypirc file ready

	```
	[distutils]
	index-servers=
    pypi
    pypitest

	[pypitest]
	#repository = https://testpypi.python.org/pypi
	repository = https://test.pypi.org/legacy/
	username = <my pypitest username>
	password = <my pypitest password>

	[pypi]
	#repository = https://pypi.python.org/pypi
	repository = https://upload.pypi.org/legacy/
	username = <my pypi username>
	password = <my pypi password>

	```

- Install build and publish tools
```bash
python -m pip install build twine
```

## Steps

1. Merge your branch into master
  (you want tags to be point t a commit in master)

	`git checkout master`
	`git merge develop`

2. List your current tags

	`git tag`


3. tag the current X.Y.Z release. We use the annotated tags
to upload them to GitHub and mark releases there as well.

	- If it is a bug, then increment Z. 
	- If it is a minor change (new feature), then increment Y
	
	`git tag -a  X.Y.Z`

	(to delete a tag type `git tag -d <tag>`)

4. Build your package and test the packaging process

```bash
python -m build
twine check dist/*
```

5. Publish

```bash
twine upload -r twisted-mqtt dist/*
```
