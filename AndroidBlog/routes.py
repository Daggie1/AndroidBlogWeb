import secrets
import os
from  PIL import Image
from flask import render_template, flash, redirect, url_for,request,abort
from AndroidBlog.models import User,Post
from AndroidBlog import app,db,bcrypt
from flask_login import login_user,current_user,logout_user,login_required
from AndroidBlog.forms import RegistrationForm,LoginForm,Update_Account_Form,NewPostForm
#post lists


def save_picture(form_picture):
        random_hex=secrets.token_bytes(8)
        file,file_extension=os.path.splitext(form_picture.filename)
        picture_filename=file+file_extension
        picture_path=os.path.join(app.root_path,'static/img/users',picture_filename)
        #resize
        out_put_size=(125,125)
        image=Image.open(form_picture)
        image.thumbnail(out_put_size)

        image.save(picture_path)
        return picture_filename

@app.route("/")
@app.route("/home")
def home():
    page=request.args.get('page',1,type=int)
    posts=Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=5)
    return render_template('home.html',posts=posts)
@app.route("/about")
def about():

	return render_template('about.html',title='Flaskblog--About')




@app.route("/register", methods=['GET', 'POST'])
def register():
        if current_user.is_authenticated:
            return  redirect(url_for('home'))
        form=RegistrationForm()
        if form.validate_on_submit():
            hashed_password=bcrypt.generate_password_hash(form.password.data)
            user=User(username=form.username.data,email=form.email.data,password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash(f'Your Account has been created you can now login!', 'success')
            return redirect(url_for('login'))
        return render_template('register.html',  title='Register', form=form)

@app.route("/login", methods=['GET','POST'])

def login():
        if current_user.is_authenticated:
            return  redirect(url_for('home'))
        form = LoginForm()
        if form.validate_on_submit():
            user=User.query.filter_by(email=form.email.data).first()
            if user and bcrypt.check_password_hash(user.password,form.password.data):

                login_user(user,remember=form.remember.data)
                next_page=request.args.get('next')
                return redirect(next_page)if next_page else redirect(url_for('home'))
            else:
                flash(f'Unsuccessful login please check your password or email','danger')
        return render_template('login.html', form=form)
@app.route("/logout")
def logout():
    logout_user()
    return   redirect(url_for('home'))
@app.route("/account",methods=['GET', 'POST'])
@login_required
def account():
    form=Update_Account_Form()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file=save_picture(form.picture.data)
            current_user.img_file=picture_file
        current_user.email=form.email.data
        current_user.username=form.username.data
        db.session.commit()
        flash(f'Your Account has been updated!',category='success')
        return redirect(url_for('account'))
    elif request.method=='GET':
        form.username.data=current_user.username
        form.email.data=current_user.email
    img_file=url_for('static' ,filename='img/users/'+current_user.img_file)
    return render_template('account.html' ,form=form,img_file=img_file)
@app.route("/post/new_post", methods=['GET', 'POST'])
@login_required
def new_post():
     form=NewPostForm()
     if form.validate_on_submit():
         post=Post(title=form.title.data,content=form.content.data,author=current_user)
         db.session.add(post)
         db.session.commit()
         flash(f'Post added!', category='success')
         return redirect(url_for('home'))
     return render_template('new_post.html',form=form,title='New Post' ,legend='New Post')
@app.route("/post/<int:post_id>")
def post_details(post_id):
     post=Post.query.get_or_404(post_id)
     return render_template('post_details.html',post=post,title=post.title)

@app.route("/post/<int:post_id>/update",methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = NewPostForm()
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()
        flash(f'Your post has been updated!', category='success')
        return redirect(url_for('post_details',post_id=post.id))
    elif request.method=='GET':
        form.title.data=post.title
        form.content.data=post.content
    return render_template('new_post.html', form=form,tiltle='Update Post',legend='Update Post')
@app.route("/post/<int:post_id>/delete",methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()