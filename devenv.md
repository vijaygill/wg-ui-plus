## Developer environment ##
* Have 3 SSH terminals running and cd to the directory where the repo is cloned.
  * If running for first time after cloning
    * Execute following command
      ```
      ./build-dev-run-bash.sh
      ```
    * In the bash shell (in the container) run following command to install all npm packages
      ```
      cd /wg-ui-plus/app/wg-ui-plus
      npm install
      ```
    * Exit from the shell (and thus the container also).

* In first terminal, execute following command. This will build the Angular app for the first time and keep "ng" running in watch mode for any more changes. That's my lazy way of "ng build" :).
  ```
  ./build-dev-run-ng-build.sh
  ```

* In the second terminal, run following command. This will start the python-flask app which can be accessed from the browser (see the port in the following script file).
  ```
  ./build-dev-run-app-serve.sh
  ```

* Now in third terminal, use your favourite editor to edit the files! I use vim. If you are using GUI (KDE/Gnome), you don't need third terminal and you can use any GUI editor.

## Remember: ##
* Always have a branch for every new feature. The "develop" branch is supposed to be semi-stable. But keep it stable as much as possible.
