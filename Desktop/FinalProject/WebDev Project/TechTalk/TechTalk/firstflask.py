import os
import secrets
from flask import Flask, render_template, url_for, flash, redirect, request, jsonify, abort
from flask_migrate import Migrate
from extensions import db, login_manager
from forms import (RegistrationForm, LoginForm, UpdateAccountForm, PostForm, 
                   CommentForm, FollowRequestForm, AcceptFollowRequestForm, 
                   DeclineFollowRequestForm, GroupForm)
from models import User, Post, Comment, FollowRequest, Group, GroupMember
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user, logout_user, login_required


app = Flask(__name__)
migrate = Migrate(app, db)
app.config.from_object('config.Config')

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def save_picture(form_picture, folder):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/uploads', folder, picture_fn)

    try:
        form_picture.save(picture_path)
    except Exception as e:
        print(f"Error saving picture: {e}")
        raise

    return picture_fn

@app.route('/api/posts/<int:post_id>', methods=['GET'])
@login_required
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    post_data = {
        'title': post.title,
        'content': post.content,
        'author': post.author.username,
        'date_posted': post.date_posted.strftime('%Y-%m-%d %H:%M:%S'),
        'likes': post.likes.count(),
        'comments': [{'author': comment.author.username, 'content': comment.content} for comment in post.comments]
    }
    return jsonify(post_data)

@app.route('/')
@app.route('/home')
@login_required
def home():
    followed_users = current_user.followed.all()
    posts = Post.query.filter(
        Post.user_id.in_([user.id for user in followed_users]) | (Post.user_id == current_user.id)
    ).order_by(Post.date_posted.desc()).all()
    
    return render_template('home.html', posts=posts, form=CommentForm())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, hide_navbar=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        flash('Login unsuccessful. Please check email and password', 'danger')
    
    return render_template('login.html', form=form, hide_navbar=True)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/profile/<username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data, 'profile_pics')
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('profile', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    image_file = url_for('static', filename='uploads/profile_pics/' + user.image_file)
    
    posts = user.posts if user == current_user or current_user.is_following(user) else []
    
    return render_template('profile.html', user=user, form=form, image_file=image_file, posts=posts)

@app.route('/search')
@login_required
def search():
    query = request.args.get('query', '')
    results = User.query.filter(User.username.ilike(f'%{query}%')).all() if query else []
    return render_template('search.html', query=query, results=results)
   
@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        image_file = save_picture(form.image.data, 'post_images') if form.image.data else None
        video_file = save_picture(form.video.data, 'post_videos') if form.video.data else None

        post = Post(
            title=form.title.data, 
            content=form.content.data, 
            image_file=image_file, 
            video_file=video_file, 
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('post.html', form=form)

@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user.has_liked_post(post):
        flash('You have already liked this post.', 'info')
    else:
        post.likes.append(current_user)
        db.session.commit()
        flash('You have liked the post.', 'success')
    return redirect(url_for('home'))

@app.route('/post/<int:post_id>/unlike', methods=['POST'])
@login_required
def unlike_post(post_id):
    post = Post.query.get_or_404(post_id)
    if not current_user.has_liked_post(post):
        flash('You have not liked this post yet.', 'info')
    else:
        post.likes.remove(current_user)
        db.session.commit()
        flash('You have unliked the post.', 'success')
    return redirect(url_for('home'))

@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    comment = Comment(content=content, author=current_user, post=post)
    db.session.add(comment)
    db.session.commit()
    flash('Your comment has been added.', 'success')
    return redirect(url_for('home'))

@app.route('/send_follow_request/<int:user_id>', methods=['POST'])
@login_required
def send_follow_request(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot send a follow request to yourself!', 'danger')
    elif FollowRequest.query.filter_by(sender_id=current_user.id, receiver_id=user.id).first():
        flash('Follow request already sent.', 'info')
    else:
        follow_request = FollowRequest(sender=current_user, receiver=user)
        db.session.add(follow_request)
        db.session.commit()
        flash(f'Follow request sent to {user.username}.', 'success')
    return redirect(url_for('profile', username=user.username))

@app.route('/accept_follow_request/<int:request_id>', methods=['POST'])
@login_required
def accept_follow_request(request_id):
    follow_request = FollowRequest.query.options(
        db.joinedload(FollowRequest.sender),
        db.joinedload(FollowRequest.receiver)
    ).get_or_404(request_id)

    if follow_request.receiver_id != current_user.id:
        flash('You cannot accept this follow request.', 'danger')
    else:
        current_user.accept_follow_request(follow_request)
        flash(f'Follow request from {follow_request.sender.username} accepted.', 'success')

    return redirect(url_for('follow_requests'))


@app.route('/decline_follow_request/<int:request_id>', methods=['POST'])
@login_required
def decline_follow_request(request_id):
    follow_request = FollowRequest.query.get_or_404(request_id)
    if follow_request.receiver_id != current_user.id:
        flash('You cannot decline this follow request.', 'danger')
    else:
        db.session.delete(follow_request)
        db.session.commit()
        flash('Follow request declined.', 'info')

    return redirect(url_for('follow_requests'))

@app.route('/follow_requests')
@login_required
def follow_requests():
    try:
        follow_requests = FollowRequest.query.filter_by(receiver_id=current_user.id).all()
        return render_template('follow_requests.html', follow_requests=follow_requests)
    except Exception as e:
        
        print(f"Error retrieving follow requests: {e}")
        return render_template('follow_requests.html', follow_requests=[])

@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route('/unfollow_user/<int:user_id>', methods=['POST'])
@login_required
def unfollow_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot unfollow yourself!', 'danger')
    elif not current_user.is_following(user):
        flash('You are not following this user!', 'info')
    else:
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You have unfollowed {user.username}.', 'success')
    return redirect(url_for('profile', username=user.username))


@app.route("/group/<action>", methods=['GET', 'POST'])
@app.route("/group/<action>/<int:group_id>", methods=['GET', 'POST'])
@login_required
def group(action, group_id=None):
    form = GroupForm()
    if action == 'create':
        if form.validate_on_submit():
            group = Group(name=form.name.data, description=form.description.data, creator=current_user)
            db.session.add(group)
            db.session.commit()
            flash('Your group has been created!', 'success')
            return redirect(url_for('group', action='list'))
        return render_template('groups.html', action=action, form=form)
    
    elif action == 'details' and group_id:
        group = Group.query.get_or_404(group_id)
        
        if current_user not in group.members:
            flash('You must be a member of the group to view its details.', 'warning')
            return redirect(url_for('group', action='list'))

        posts = Post.query.filter_by(group_id=group_id).all()
        post_form = PostForm()
        if post_form.validate_on_submit():
            post = Post(title=post_form.title.data, content=post_form.content.data, author=current_user, group_id=group.id)
            db.session.add(post)
            db.session.commit()
            flash('Your post has been created!', 'success')
            return redirect(url_for('group', action='details', group_id=group_id))
        return render_template('groups.html', action=action, group=group, posts=posts, form=post_form)
    
    elif action == 'members' and group_id:
        group = Group.query.get_or_404(group_id)
        
        if current_user not in group.members:
            flash('You must be a member of the group to view its members.', 'warning')
            return redirect(url_for('group', action='list'))

        members = group.members
        return render_template('groups.html', action=action, group=group, members=members)
    
    elif action == 'list':
        groups = Group.query.all()
        return render_template('groups.html', action=action, groups=groups)
    
    else:
        abort(404)



@app.route("/group/post/<int:group_id>", methods=['POST'])
@login_required
def post_in_group(group_id):
    group = Group.query.get_or_404(group_id)
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user, group_id=group.id)
        if form.image.data:
            image_file = save_image(form.image.data)
            post.image_file = image_file
        if form.video.data:
            video_file = save_video(form.video.data)
            post.video_file = video_file
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('group', action='details', group_id=group_id))
    return render_template('groups.html', action='details', group=group, form=form)

@app.route("/group/join/<int:group_id>", methods=['POST'])
@login_required
def join_group(group_id):
    group = Group.query.get_or_404(group_id)
    
    if current_user in group.members:
        flash('You are already a member of this group.', 'warning')
        return redirect(url_for('group', action='details', group_id=group_id))
    
    group.members.append(current_user)
    db.session.commit()
    
    flash('You have joined the group!', 'success')
    return redirect(url_for('group', action='details', group_id=group_id))


@app.route("/group/leave/<int:group_id>", methods=['POST'])
@login_required
def leave_group(group_id):
    group = Group.query.get_or_404(group_id)
    
    if current_user not in group.members:
        flash('You are not a member of this group.', 'warning')
        return redirect(url_for('group', action='list'))
    
    
    group.members.remove(current_user)
    db.session.commit()
    
    flash('You have left the group!', 'success')
    return redirect(url_for('group', action='list'))

if __name__ == '__main__':
    app.run(debug=True)
