Server client communication

the fetch-push methods are symmetric.
one time the client requests and server sends,
the other time client sends and server requests.\


essentially, there are two ways of server-client communications.
1. through the server panel: which allows you the create and delete repositories.
2. through the fetch-pull interaction which is described later.


push:
    client provides a repository id and an authentication token
    server sends the hash tree he has
    client sends the files that are missing
    after the client has finished sending the files, it requests that the server applies them


The LOOT protocol

authentication:
    user sends an authentication token to a repository (probably RSA private key)
    server checks if the private key matches the public key connected to a repo
    communications continue...

creating repository:
    client sends a request to create a repo and provides a public key to be correlated with the local private key
    server responses accordingly







