# Budget Eats
#### Video Demo: https://www.youtube.com/watch?v=UXriwfB74g0

## Summary
Budget Eats is a flask application that aims to promote food, cooking, and healthy diet to students at a reasonable price. The backend is written in python with a SQLite database; the frontend is written using HTML and CSS, which are aided by Bootstrap 4 and Jinja templating. Dynamic features on the frontend have been created utilising both plain JavaScript and JQuery. Along with supporting account services, the website has three main features:
1. [Menu](#menu) : Food delivery service
2. [Shop](#shop) : Kitchen accessories
3. [Blog](#blog) : Food blog & product discussion

This document will aim to briefly introduce the function of each page, while highlighting any features that are unique to that route. Please visit these links for more information about [login services](#login-services) or the [account dashboard](#account-dashboard).

## Common Features & Homepage
The common features in the application, such as the header and footer, are placed in a single HTML file that is shared across all routes using the [Jinja "extends"](https://jinja.palletsprojects.com/en/3.0.x/templates/) keyword. This creates a "skeleton" that every route builds upon without having needless repetition.

### Favicon Icon
Adding a relevant emoji to the website tab helps create a more polished feel for the website. This is achieved through the use of a [favicon icon emoji](https://favicon.io/emoji-favicons/fork-and-knife-with-plate). The icon is stored in the static section of the application directory, which is linked in the head of the layout html file for application-wide access.

<img src="/readme_images/favicon.png" width="400px">

### Header
The header contains the navigation tools for the whole website. Taking heavy inspiration from CS50 Finance's bootstrap navbar, links to all the main content of the website are available on left. On the right a [font awesome](https://fontawesome.com/v4/) icon is used to link the user to their shopping basket, along with a bootstrap dropdown menu greeting the user; this contains links to the users [account dashboard](#account-dashboard) and logout. If the user is logged out the content on the right is instead replaced with Log In and Register options.

<img src="/readme_images/navbar.png" width="400px">

### Homepage
The homepage is the first impression for the whole website and as such contains many links and eye grabbing features, aimed to quickly inform the user of the websites functionality. On loading the user will be greeted with a short introduction and a bootstrap carousel that links to each of the three main website features.

<img src="/readme_images/homepage1.png" width="400px">

This is followed up with more information about the food delivery service as well as a selection of three products from the [shop](#shop). These items are randomised from the product database, with the only requirement being that they are still in stock. These products are randomised every time the page is loaded.

<img src="/readme_images/homepage2.png" width="400px">

### Footer
Utilising relative positioning and content-wrap for the other contents of the page, a sticky footer is created that remains at the bottom of the page if the content is short, while only being visible once the user has scrolled all the way to the bottom on longer pages. The footer contains links to support and FAQ pages, as well as [font awesome](https://fontawesome.com/v4/) social media links.

<img src="/readme_images/footer.png" width="400px">

## Menu
This section of the application deals with taking user input for their food preferences and allergies, before outputting a customised menu from which the user can pick meals to purchase. Users may recieve a quote without being logged in but will be prompted to log in or register if they wish to proceed further. If a user is logged in and has previously entered their preferences and allergy choices, they will be directed straight to [meal choice](#meal-choice) with their preferences settings taken from the database.

### Quote
Two interactive sliders take input of the number of meals the user wishes to order, as well as the number of people for which they wish to cook. This information is then sent to the backend via an AJAX call and a quote price returned for display to the user. Once a user is happy with their quote they may submit to save their input to the database and continue with the process if they are logged in. A logged out user will be redirected to log in or register should they wish to continue with their purchase.

<img src="/readme_images/quote.png" width="400px">


### Preferences
The user will input their dietary requirements via radio buttons, followed by selecting any allergies they may have from the list of checkboxes. Upon continuing these inputs are stored on the database.

<img src="/readme_images/preferences.png" width="400px">

### Meal Choice
At this point the user has inputted all the required information to recieve their personalised menu. The recipes database is queried using the users preferences and allergies to filter out unsuitable meals, and displayed to the user via a bootstrap card deck nested within a carousel. The user can then browse the different meals available to them; selecting the meals they wish to choose via checkbox. The number of meals currently selected is displayed at the top of page using JavaScript, and the submit button is enabled when the user has selected the the amount of meals previously selected in [quote](#quote). The user also has the option to review or change their preferences at any time via link to [my preferences](#my-preferences) at the top of the page.

<img src="/readme_images/menu.png" width="400px">

### Food Checkout
This route displays the selected meals in a table to the user, as well as the number of people the meals will serve. Below this is a form requiring delivery and payment details. The validity of the card number is checked via the credit function created in week 1. Once all required information has been provided the order and all associated information is stored on the database and the order is completed. Upon completion the user gains access to the relevant recipes for their order in [my recipes](#my-recipes).

<img src="/readme_images/food_checkout.png" width="400px">

### Food Invoice
A flashed message confirms to the user that their order is complete, and the page displays all relevent information pertaining to the order in the form of an invoice. A copy of this invoice is also sent to the on-file email address of the user via `Flask-Mail`.

<img src="/readme_images/food_invoice.png" width="400px">

## Shop
This section of the application is a classic online shop, with an array of items each of which can be purchased and reviewed. Users can view the shop and its products, along with the respective reviews, without being logged in. Upon attempting to add an item to their basket the user will at this point be requested to log in or register.

### Shop Browse
The route for browsing all available items, a grid of products is displayed to the user with a picture of the product as well as the price and average review rating. Each product is displayed in a bootstrap card that links to the respective product page.

<img src="/readme_images/shop.png" width="400px">

### Product
Route that displays product details for the selected product. First half of the page has extensive product information as well as the add to basket option. The quantity select option is dynamically generated using jinja statements in the html page, the range of which changes dependant upon the remaining stock of the item. The sub-total for X amount of the product is dynamically updated via AJAX call as the quantity is changed. If the user is logged in and adds an item to their basket the product ID and quantity are added to the basket session variable for later access in the form of a dictionary.

<img src="/readme_images/product1.png" width="400px">

The second half of the page displays all relevant review and rating data for the product. A detailed breakdown of all the ratings for the product is provided on the left, as well as a display of the users own review. Further details about this feature can be found in [reviews](#reviews). Below this are the remaining product reviews which are ordered by star rating.

<img src="/readme_images/product2.png" width="400px">

### Basket
This route takes the contents of the session basket variable and displays them back to the user in the form of a table, again utilising jinja syntax in the html page to create select elements that already have the requested quantity on page load. The quantity of each item can be changed, and the total cost dynamically updated via AJAX call. Items can also be removed from the list via POST form submission. Once a user is content with their item selection they can submit the form to progress with their order.

<img src="/readme_images/basket.png" width="400px">

### Shop Checkout
This route is identical to its [food order equivalent](#food-checkout). Chosen products are displayed in a table with a total cost for the user to double check. Below is a form requesting delivery address and payment information. Form can be submitted via POST to complete the order by storing all order and relevant data on the database.

<img src="/readme_images/shop_checkout.png" width="400px">

### Shop Invoice
Again this is practically identical to its [counterpart](#food-invoice) in food orders. Notify the user of the completed order via flashed message, along with an invoice with all order details. A copy of this invoice is also sent to the on-file email address of the user via `Flask-Mail`.

<img src="/readme_images/shop_invoice.png" width="400px">

### Reviews
Reviews for products can be created when a logged in user is verified to have purchased a product. If a user is not logged in, the user review section of the [product page](#product) will prompt them to log in. If a user has already reviewed that product their review will be displayed, otherwise a link to create a review will be displayed.

Once a user reaches the create-review route the users order history will be checked on the database. If the user has purchased the product they will complete a form creating a review for the product. If the user has not purchased the product they will be denied access and prompted to visit the shop.

<img src="/readme_images/create_review.png" width="400px">

Once the review has been created and stored in the reviews table on the backend, the review will be displayed along with any others on the [product page](#product). From here the user will be allowed to edit (user will be redirected to an autofilled form to edit current review content) or to delete the review. These options require confirmation via the javascript confirm function before being allowed to continue away from the page. e.g. `onsubmit="return confirm('Really delete your review?')"`

## Blog
This section of the application allows users with a verified email address to create blog posts and comments; as well as the opportunity to like or dislike content. Users that are not logged in can view any blog post and its respective comments by searching the browse page, but will be requested to log in or register if they wish to contribute to the blog.

### Browse
Main page of the section that allows users to search through all blog content. Blog posts are ordered by the last interaction i.e. how long ago a post has been created or commented on. The list of posts is split up into pages and fully sortable via [DataTables](https://datatables.net/). Create post link at the top of the page is disabled using JavaScript if user is either logged out or does not have a verified email address, with links provided to either log in or request a new verification link.

<img src="/readme_images/blog_browse.png" width="400px">

### Create Post
This route provides verified users with the create post form. If a user types this route directly into the url in an attempt to bypass the email verification restrictions they will be redirected to the [verification request](#verify-request) route due to a verification required function wrapper.

<img src="/readme_images/create_post.png" width="400px">

### Post
Route that displays blog post and all relevant comments to the user.

#### Post Content
The top of the page contains all post content and details along with options to edit or delete the post if the post author is signed in. Edit post takes the user to another page with a form that is autofilled with the current content. If a post has been edited this is also shown on the right hand side along with a timestamp for transparency. Delete post is handled via POST form submission which deletes all relevant post, comment, and comment voting data on the database.

<img src="/readme_images/post1.png" width="400px">

#### Comment Section
Below the post content is the comment section. Here a user may create a comment if they meet the criteria via a [bootstrap collapse](https://getbootstrap.com/docs/4.0/components/collapse/) form that may be hidden or shown for a tidier UI. As with other restricted blog features, if a user is not logged in and verified they are provided with links to gain full access to the website.

<img src="/readme_images/post2.png" width="400px">

The comments themselves also have edit and delete options for the author. Editing a comment utilises jQuery to edit the html of the page; allowing the user to submit the edit comment form via POST without leaving the page. As before, delete removes all associated voting data in the database upon deletion of the parent comment. Finally, users may vote on any comment if they are logged in, with a users_comments join table allowing for a many to many relationship database that keeps track of each users voting status for each comment.

<img src="/readme_images/post3.png" width="400px">

## Login Services

### Login and Register
These routes provide forms for account creation and access, with the login page being the redirect route for the login required function wrapper. The wrapper is customised such that if a user is forced to log in for access to a feature (e.g. [quote](#quote)), they will be returned back to the page they were on upon logging in or registering. This is achieved by allowing these routes to accept a varying number of arguments in the url, with the default behaviour being to redirect to the home page.

### Email Verification
When registering an account for the first time the user will be redirected to the homepage accompanied by a flashed message directing them to check their email account for a verification email. By default the verified boolean variable is set to false and can only be set to true through the verify route. This route takes a time sensitive token generated by the [itsdangerous](https://itsdangerous.palletsprojects.com/en/2.1.x/) `URLSafeTimedSerializer` function. This gives the user 60 minutes to verify their account before the link will no longer be valid. If the user logs in again in the future and has still failed to verify their email address they will be prompted to check their email or request a new token via flashed message.

<img src="/readme_images/verify.png" width="400px">

If a token is invalid the user will be informed and redirected to the verify_request route. Here extra tokens can be requested at any time by unverified users.

### Forgotten Password
If a user forgets their password they may request a password reset email to be sent to their email address. The input email address is searched on the database and if an account with this email exists another time sensitive itsdangerous token will be generated and sent to the email address.

## Account Dashboard
The account dashboard is a hub for anything the user may wish to change about their account. This route supplies links to change account details, access food delivery settings and recipes, and the full history of all account activity. This is accessed via the dropdown menu in the right of the [header](#header).

### Account details

#### Email Change
If a user wishes to change their email address they may do so through this route. A new email address will be requested and confirmed along with the current account password. On doing so the itsdangerous serializer will again be used to generate a token that will be sent to the *new* email address that contains both the old and new email addresses. Upon following this link back to the website, the token will be deserialized and the two email addresses used to update the database. A final email will be sent to the *old* email address informing the user of the change for account security purposes.

#### Password Change
Similarly this route allows the user to change their password. Inputting and confirming a new password along with the old password completes the change. As before, an email is sent to the account's email address for account security purposes.

### Food Options

#### My Preferences
Here a user may review all of their current food settings. This includes number of meals, servings, as well as all dietary and allergy preferences. The user is also given the option to update these settings, which redirect them back to [quote](#quote) and [preferences](#preferences).

<img src="/readme_images/my_preferences.png" width="400px">

#### My Recipes
This is the route where the user's purchased recipes are stored for them to browse. Each recipe is displayed in the form of a bootstrap card, and the list may be filtered by entering a string into the searchbox at the top of this page. This is achieved using a keyup event  listener that filters out all cards that do not contain the input string. This search is case insensitive.

<img src="/readme_images/my_recipes.png" width="400px">

### Account History
Each of the different parts of the history section contain tables of the users activity on the platform. Each table is styled using [DataTables](https://datatables.net/) to provide the user with the means to sort and search through their data across multiple pages.

#### My Orders
This route handles both the food and shop order history. This is achieved through a toggle button at the top of the page that hides/shows the appropriate table when clicked. Each table entry gives details pertaining to the orders along with a link to the invoice page. These invoice pages are identical to the ones supplied earlier in the application ([Food Invoice](#food-invoice), [Shop Invoice](#shop-invoice)).

<img src="/readme_images/orders.png" width="400px">

#### My Reviews
This table links the user to any reviews that they have left on products, along with all relevant information.

<img src="/readme_images/reviews.png" width="400px">

#### Blog History
Similarly to order history, this page deals with all blog interactions for both posts and comments. Again the table content is toggled via buttons that hide and show html content.

<img src="/readme_images/blog_history.png" width="400px">

## TODO List
The following features have been considered but deemed to be outside of the scope of the project for now.
1. Improved order history functionality
   - Display all items in the order via drop down "more details" button
   - Direct link to invoice
   - Print invoice button on each invoice page
2. Turn the food delivery into a subscription service
   - Allow one selection per week
   - Charge once per week
   - Reminder emails to choose upcoming meals
3. Autofill destination/payment data for recurring users
   - Option to use new info/use old info
   - Add my saved payments/destinations to account dashboard
4. Add visualisations of the database structure to readme
