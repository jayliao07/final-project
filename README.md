Final Project Developer Guide
===========================================================

Jiacheng Liao

This markdown file is nicer displayed online(such as Github page) than in a text editor.

Git Repo: https://github.com/miracleoops/final-project

Google appspot url: http://firstpyproj-1057.appspot.com/


# For Grader

##Note
	

 1. Please test the app using Google Chrome. (some of the javascript may not work on other browsers, such as check empty input, disable edit button, etc).
 2. After adding new a resource, editing a resource, making a reseravation you will be redirected to home. You can also click Home button at the top nav-bar anytime to go home.
 3. Sometimes it may happen that after adding or editing, the datastore is a little bit slower and thus the home doesn't show correct resources/reservations. You maybe need wait a second or refresh the home page.

## Basic Features

 1. Muliple User
 2. After login, you can see 3 tab with all resources, your resources your coming reservations. The add resource button, search name and tags column are on the left.
 3. Done with GQL query. 
 4. Here I assume 0-24 time system when creating a resource.
 5. Here (1)(2)(3) are shown on the same page since I feel it's better for user if they can see the resource's info and recent made reservations when the user is making a reservation. If you are not the owner of the resource, then edit button is disabled. 
 6. Here a start time and end time is used for reservation like resources. (Equivalent of start time and duration)
 7. A user can see his/her reservations on the homepage. 
 8. Delete reservation can be done via delete button on your reservations tab.
 9. You can see resources of a given tag in "All resources available" tab. (note: To cancel effect of tags, click Home button at top)
 10. RSS button

## Extra Credit Feature

 - Support the ability to search for resources by name. (Similar to tag search)
 - Support a requirement where a user can only have one reservation at a time.
