# Edge cases
At the initial stage of development, there were few things that could be treated differently. I decided to go simple, with quick buy still logic solutions. As the first example, should any user, be able to delete all the other users, or just himself? 
I presume that only the owner of the account should be able to update or delete account, despite the task is not elaborating about that.  

As we are with users, lets take look at them.  

- For instance role can be defined ad boolean(for example value true if its seller), however this will close our path to possible extedt, as we could add new roles in the future.  

- Could one user be buyer and seller?  Make some sense in real world, yet here  one account has one role.  

- Usually one seller is logged in one place, thus we don't need to asure change products in transaction blocks. 
- If its hard requirement that only seller can edit product, than it make sense to allow owner to transfer ownership.
- What about products, that were added by seller, who gets removed ? Will they dangle? Should they be removed ? Can be edited, if yes, by who ?
- Does anyone should be able to register himself as seller or buyer ? Or it should be handled in special way ?
- Should deposit of a new registered buyer be 0, or should we allow to set it ?
- What should we allow to edit during update user ?

More questions
- Do we have infinite change for users, when they dont have enought coins of required kind ?
- How much product they can buy in one transaction ?
- How much of coins they can store within machine ?
- Is there any max storedge capacity inside machine ?

### Concurrent
API can be used concurently by different users(both sellers and buyers) but it is designed to handle only one vending machine.
We should use database other than sqlite to provide correct working transaction mechanism.

### In addition(more work)
- We should also ask for email.
- Password is not handled in any special way(passing around as plaintext).
- Secrets should be moved to possibly .env file.

### Sessions
Current /logout/all/ implementation remove session information from db, so we are loosing some of the information, like when user has logged in.

### And finally  
HEAD and OPTIONS are default allowed for CRUD's, but can be easly disallowed