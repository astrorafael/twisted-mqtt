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
	repository = https://testpypi.python.org/pypi
	username = <my pypitest username>
	password = <my pypitest password>

	[pypi]
	repository = https://pypi.python.org/pypi
	username = <my pypi username>
	password = <my pypi password>

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

4. Register the new release in testing PyPi website

	`sudo python setup.py register -r pypitest`
	
5. Package and Upload at the same time in testing PyPi website

	`sudo python setup.py sdist upload -r pypitest`

6. Test that you can install it from the Testing PyPi site

	`sudo pip install -i https://testpypi.python.org/pypi <package name>`

7. Do 3 through 5 with the normal PyPi website

	`sudo python setup.py register` 
	`sudo python setup.py sdist upload`
	`sudo pip install <package name>`

# Updating GitHub repo

1. Push master branch and tags to GitHub

	`git push --tags origin master`

# Reviewing the package in PyPi

	Use your credentails in ~/.pipyrc

# Remove named tags 

	- This wil delete the tag in your local repo: `git tag -d 12345`

	- And this will delete it from GitHub: 
	
	`git tag -d 12345`
	`git push origin :refs/tags/12345`

# See also

- [Python Wiki](https://wiki.python.org/moin/TestPyPI)
- [Far McKon website](http://www.farmckon.net/tag/testpypi/)
