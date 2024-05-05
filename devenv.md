## Developer environment

Have three SSH terminals running and `cd` to the directory where the repo is cloned.

In first terminal, execute following command.
This will build the Angular app for the first time and keep "ng" running in watch mode for any more changes.
That's a lazy way of "ng build" :).
```
./run-ng
```

In the second terminal, run following command.
This will start the `python-flask` app which can be accessed from the browser (see the port in the following script file).
```
./run-app-server
```

Now in third terminal, use your favorite editor to edit the files!
I use `vim`.
If you are using GUI (KDE/Gnome), you don't need third terminal and you can use any GUI editor.
To facilitate easier access to `ng` commands, and ensure you've any other tools/packages for development, you probably want to run
```
./run-dev-sh
```

## Branching Strategy

Always have a branch for every new feature and give it a meaningful name.
For example, `feature/readme-updates`.

When trying out more 'ad-hoc experiments', use the `experimental/` pre-fix, ie `experimental/port-to-rust`.
The experimental branches may get 'promoted' to features, or just dropped.
Don't feel like you must use experimental branches first, use your best judgment.

The `develop` branch is supposed to be semi-stable, but keep it stable as much as possible.
builds on this branch are akin to 'beta versions', ideally they will be fine to use, but who knows.
When merging into the `develop` branch, we shall squash merge; 
the `feature/` branch can happily have all the messy commits you want, but when merged, a nice clean message can be provided.

The `main` branch is for release versions.
In theory, these builds are perfectly stable and gone through testing.
Merging into `main` will only be done from `develop`, then a GitHub release created to stamp a new version.
Each version on `main` will have it's Docker image pushed to a repo, along with the 'latest' tagged updated to... well, the latest build.
